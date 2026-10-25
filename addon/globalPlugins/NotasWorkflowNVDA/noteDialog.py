# -*- coding: UTF-8 -*-
# NotasWorkflowNVDA - noteDialog.py
# "New note" and the note window: title, location (notebook or folder), status,
# content, formatting and automatic saving. Tags are no longer shown (1.7.0): the
# ones a note has stay in the file as they are.
# Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
# This file is covered by the GNU General Public License, version 2.

import addonHandler
import wx
from gui import guiHelper

from . import markup, messages, model
from .locationTree import LocationTree
from .store import StoreError

addonHandler.initTranslation()

#: Formats of the Formatting menu.
MENU_FORMATS = markup.FORMATS
SHORTCUTS = {"bold": "Ctrl+B", "italic": "Ctrl+I"}


def chooseFormat(window):
	"""Shows the Formatting menu and returns the chosen format (or None).
	A module function so the tests can replace it."""
	menu = wx.Menu()
	ids = {}
	for kind in MENU_FORMATS:
		label = messages.formatName(kind, True)
		if kind in SHORTCUTS:
			label += "\t" + SHORTCUTS[kind]
		item = menu.Append(wx.ID_ANY, label)
		ids[item.GetId()] = kind
	chosen = []
	menu.Bind(wx.EVT_MENU, lambda evt: chosen.append(ids.get(evt.GetId())))
	window.PopupMenu(menu)
	menu.Destroy()
	return chosen[0] if chosen else None


class NewNoteDialog(wx.Dialog):
	def __init__(self, parent, store, laneId=model.DEFAULT_LANE, notebookId=None, folderId=None):
		# Translators: title of the window that creates a note.
		super().__init__(parent, title=_("New note"))
		self.store = store
		sHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		# Translators: label of the title field of a note.
		self.titleEdit = sHelper.addLabeledControl(_("&Title:"), wx.TextCtrl, size=(380, -1))
		self.titleEdit.SetMaxLength(model.MAX_TITLE)
		# Translators: label of the tree with the place of a note: loose, a folder or a notebook (inside its folder).
		self.locationTree = sHelper.addLabeledControl(_("&Location:"), LocationTree, store=store)
		self.locationTree.setPlace(store.location(notebookId, folderId))
		# Translators: label of the status (lane) box of a note.
		self.laneChoice = sHelper.addLabeledControl(_("&Status:"), wx.Choice, choices=messages.laneNames())
		self.laneChoice.SetSelection(model.laneIndex(laneId))
		buttons = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: button that creates the note.
		self.createButton = buttons.addButton(self, id=wx.ID_OK, label=_("C&reate"))
		# Translators: button that closes a window without doing anything.
		self.cancelButton = buttons.addButton(self, id=wx.ID_CANCEL, label=_("Cancel"))
		sHelper.addItem(buttons, flag=wx.ALIGN_RIGHT)
		main = wx.BoxSizer(wx.VERTICAL)
		main.Add(sHelper.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL | wx.EXPAND)
		self.SetSizer(main)
		main.Fit(self)
		self.createButton.SetDefault()
		self.titleEdit.Bind(wx.EVT_TEXT, self.onTitle)
		# Enter in the Location tree creates the note, as in the other fields.
		self.locationTree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, lambda evt: self.create())
		self.onTitle(None)
		self.CentreOnScreen()
		self.titleEdit.SetFocus()

	def onTitle(self, evt):
		self.createButton.Enable(bool(self.titleEdit.GetValue().strip()))

	def create(self):
		if self.createButton.IsEnabled():
			self.EndModal(wx.ID_OK)

	def values(self):
		notebookId, folderId = self.locationTree.place()
		return {
			"title": self.titleEdit.GetValue().strip(),
			"notebookId": notebookId,
			"folderId": folderId,
			"laneId": model.LANE_IDS[max(0, self.laneChoice.GetSelection())],
		}


class NoteDialog(wx.Dialog):
	"""The note window. Saves by itself some seconds after the last change and
	always saves what is pending when it is closed."""

	def __init__(self, parent, plugin, noteId):
		self.plugin = plugin
		self.noteId = noteId
		note = self.store.getNote(noteId)
		super().__init__(parent, title=messages.noteTitle(note), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		self.dirty = set()
		self._loading = True
		sHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		# Translators: label of the title field of a note.
		self.titleEdit = sHelper.addLabeledControl(_("&Title:"), wx.TextCtrl, size=(520, -1))
		self.titleEdit.SetMaxLength(model.MAX_TITLE)
		# Translators: label of the tree with the place of a note: loose, a folder or a notebook (inside its folder).
		self.locationTree = sHelper.addLabeledControl(_("&Location:"), LocationTree, store=self.store, size=(520, 150))
		# Translators: label of the status (lane) box of a note.
		self.laneChoice = sHelper.addLabeledControl(_("&Status:"), wx.Choice, choices=messages.laneNames())
		self.contentEdit = sHelper.addLabeledControl(
			# Translators: label of the content field of a note.
			_("&Content:"),
			wx.TextCtrl,
			style=wx.TE_MULTILINE | wx.TE_RICH2,
			size=(520, 300),
		)
		# Translators: button that opens the menu with the formats of the content (bold, lists...).
		self.formatButton = sHelper.addItem(wx.Button(self, label=_("&Formatting…")))
		self.statusEdit = sHelper.addLabeledControl(
			# Translators: label of the read-only field that says if the note is saved.
			_("Save stat&us:"),
			wx.TextCtrl,
			# Multi-line: a single-line read-only field is left out of the Tab order by wx.
			style=wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_RICH2,
			size=(520, 40),
		)
		buttons = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: button that saves the note and closes its window.
		self.saveButton = buttons.addButton(self, id=wx.ID_OK, label=_("Sa&ve and close"))
		sHelper.addItem(buttons, flag=wx.ALIGN_RIGHT)
		main = wx.BoxSizer(wx.VERTICAL)
		main.Add(sHelper.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL | wx.EXPAND, proportion=1)
		self.SetSizer(main)
		main.Fit(self)

		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)
		self.titleEdit.Bind(wx.EVT_TEXT, lambda evt: self.onChange("title"))
		self.locationTree.Bind(wx.EVT_TREE_SEL_CHANGED, lambda evt: self.onChange("location"))
		self.laneChoice.Bind(wx.EVT_CHOICE, lambda evt: self.onChange("laneId"))
		self.contentEdit.Bind(wx.EVT_TEXT, lambda evt: self.onChange("content"))
		self.formatButton.Bind(wx.EVT_BUTTON, self.onFormatButton)
		self.saveButton.Bind(wx.EVT_BUTTON, lambda evt: self.finish())
		self.Bind(wx.EVT_CHAR_HOOK, self.onCharHook)
		self.Bind(wx.EVT_CLOSE, lambda evt: self.finish())
		self.load(note)
		self.CentreOnScreen()

	@property
	def store(self):
		return self.plugin.store

	def load(self, note):
		self._loading = True
		self.titleEdit.ChangeValue(note["title"])
		self.locationTree.setPlace((note["notebookId"], None) if note["notebookId"] else (None, note["folderId"]))
		self.laneChoice.SetSelection(model.laneIndex(note["laneId"]))
		self.contentEdit.ChangeValue(markup.htmlToText(note["content"]))
		self.contentEdit.SetInsertionPoint(0)
		# Translators: save status of a note with nothing to save.
		self.statusEdit.ChangeValue(_("Saved"))
		self.dirty.clear()
		self._loading = False

	def onChange(self, field):
		if self._loading:
			return
		self.dirty.add(field)
		# Translators: save status while there are changes waiting to be saved.
		self.statusEdit.ChangeValue(_("Unsaved changes…"))
		self.timer.StartOnce(int(self.plugin.getConfig("autoSaveSeconds")) * 1000)

	def onTimer(self, evt):
		self.save(announce=bool(self.plugin.getConfig("announceAutoSave")))

	def patch(self):
		values = {
			"title": lambda: self.titleEdit.GetValue(),
			"laneId": lambda: model.LANE_IDS[max(0, self.laneChoice.GetSelection())],
			# Only an edited content is converted: imported HTML is kept as it is.
			"content": lambda: markup.textToHtml(self.contentEdit.GetValue()),
		}
		patch = {field: values[field]() for field in self.dirty if field in values}
		if "location" in self.dirty:
			notebookId, folderId = self.locationTree.place()
			patch.update(notebookId=notebookId, folderId=folderId)
		return patch

	def save(self, announce=False):
		"""Writes the pending changes. Returns False when they could not be saved."""
		self.timer.Stop()
		if not self.dirty:
			return True
		if self.store.getNote(self.noteId) is None:
			self.dirty.clear()
			# Translators: spoken when the note open in the window was deleted.
			self.plugin.speak(_("This note was deleted."))
			return False
		try:
			self.store.updateNote(self.noteId, **self.patch())
		except StoreError as e:
			# Translators: save status when the note could not be saved.
			self.statusEdit.ChangeValue(_("Not saved"))
			self.plugin.speak(messages.storeError(e, self.store.folder))
			return False
		self.dirty.clear()
		note = self.store.getNote(self.noteId)
		self.SetTitle(messages.noteTitle(note))
		# Translators: save status after saving; {time} is hours:minutes.
		text = _("Saved at {time}").format(time=messages.formatTime())
		self.statusEdit.ChangeValue(text)
		if announce:
			# Translators: spoken after the note is saved.
			self.plugin.speak(_("Note saved"))
		self.plugin.notesChanged(self.noteId)
		return True

	def finish(self):
		"""Save and close (also Esc and the window close button): nothing is lost."""
		self.save()
		self.timer.Stop()
		# Destroying the Location tree still sends a selection event: it is not a change.
		self._loading = True
		if self.IsModal():
			self.EndModal(wx.ID_OK)
		else:
			self.Destroy()

	def onCharHook(self, evt):
		key = evt.GetKeyCode()
		if key == wx.WXK_ESCAPE:
			self.finish()
			return
		if evt.ControlDown() and not evt.AltDown() and not evt.ShiftDown():
			if key == ord("S"):
				self.save()
				# Translators: spoken after Ctrl+S saves the note.
				self.plugin.speak(_("Note saved"))
				return
			if self.FindFocus() is self.contentEdit and key in (ord("B"), ord("I")):
				self.applyFormat("bold" if key == ord("B") else "italic")
				return
		evt.Skip()

	def onFormatButton(self, evt):
		kind = chooseFormat(self)
		if kind:
			self.applyFormat(kind)
		else:
			self.contentEdit.SetFocus()

	def applyFormat(self, kind):
		start, end = self.contentEdit.GetSelection()
		text, start, end, applied = markup.applyFormat(self.contentEdit.GetValue(), start, end, kind)
		self.contentEdit.SetValue(text)
		self.contentEdit.SetFocus()
		self.contentEdit.SetSelection(start, end)
		self.plugin.speak(messages.formatName(kind, applied))
