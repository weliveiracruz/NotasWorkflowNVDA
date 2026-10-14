# -*- coding: UTF-8 -*-
# NotasWorkflowNVDA - mainDialog.py
# The "Notas Workflow NVDA" window: the notes in a tree of status lanes.
# Long lanes are shown in pages, so the window stays fast with 100,000 notes.
# Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
# This file is covered by the GNU General Public License, version 2.

import addonHandler
import gui
import wx
from gui import guiHelper

from . import messages, model, prompts

addonHandler.initTranslation()

#: Notes added to a lane at a time; "Show more notes" adds the next page.
PAGE_SIZE = 200


def selectItem(tree, item):
	"""Selects an item and makes it the focused item too: Windows keeps them apart, and when the
	tree gets the focus it would go back to an old focused item (the selection would jump)."""
	tree.SelectItem(item)
	tree.SetFocusedItem(item)
	tree.EnsureVisible(item)


def escapeLabel(text):
	return text.replace("&", "&&")


class NotesDialog(wx.Dialog):
	_instance = None

	@classmethod
	def open(cls, plugin):
		if cls._instance and cls._instance.plugin is not plugin:
			cls.closeInstance()
		if cls._instance:
			# The window is kept (hidden) after Close: showing it again is instant.
			dlg = cls._instance
			if plugin.reloadIfChanged():
				dlg.refresh(dlg.selectedNoteId())
			dlg.Show()
			dlg.Raise()
			dlg.focusNotes()
			return dlg
		plugin.reloadIfChanged()
		dlg = cls(gui.mainFrame, plugin)
		cls._instance = dlg
		dlg.Show()
		dlg.Raise()
		dlg.focusNotes()
		return dlg

	@classmethod
	def closeInstance(cls):
		if cls._instance:
			cls._instance.destroy()
			cls._instance = None

	def __init__(self, parent, plugin):
		# Translators: title of the main window of the add-on.
		super().__init__(parent, title=_("Notas Workflow NVDA"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		self.plugin = plugin
		self.filters = [model.FILTER_ALL]
		self.activeFilter = model.FILTER_ALL
		self.visibleIds = []
		#: Notes shown in each lane (pages of PAGE_SIZE).
		self.shown = {}
		#: Tree items: note id -> item and lane id -> lane item (to change one note without rebuilding).
		self.items = {}
		self.laneNodes = {}
		#: True while the window is being destroyed (deleting the tree still sends events).
		self._closing = False
		#: An Enter or a double click already asked to open something (avoids opening twice).
		self._pending = False
		#: (The window is kept hidden after Close; changes reach it the same way while hidden.)
		sHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		# Translators: label of the box that chooses which notes are shown.
		self.filterChoice = sHelper.addLabeledControl(_("&Show:"), wx.Choice, choices=[])
		self.treeLabel = wx.StaticText(self, label="")
		self.tree = wx.TreeCtrl(self, size=(620, 360), style=wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS | wx.TR_LINES_AT_ROOT | wx.TR_SINGLE)
		self.root = self.tree.AddRoot("")
		sHelper.addItem(self.treeLabel)
		sHelper.addItem(self.tree, flag=wx.EXPAND, proportion=1)

		actions = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: button that opens the menu to create a note, a notebook or a folder.
		self.createButton = actions.addButton(self, label=_("&Create…"))
		# Translators: button that changes the status (lane) of the selected note.
		self.statusButton = actions.addButton(self, label=_("&Update the task status…"))
		# Translators: button that moves the selected note to a notebook or a folder.
		self.moveButton = actions.addButton(self, label=_("&Move to…"))
		# Translators: button that deletes the selected note.
		self.deleteButton = actions.addButton(self, label=_("&Delete"))
		sHelper.addItem(actions)
		actions2 = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: button that opens the search window.
		self.searchButton = actions2.addButton(self, label=_("Searc&h…"))
		# Translators: button that opens the window of notebooks and folders.
		self.organizeButton = actions2.addButton(self, label=_("Notebooks and &folders…"))
		# Translators: button that closes the window.
		self.closeButton = actions2.addButton(self, id=wx.ID_CLOSE, label=_("C&lose"))
		sHelper.addItem(actions2)

		main = wx.BoxSizer(wx.VERTICAL)
		main.Add(sHelper.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL | wx.EXPAND, proportion=1)
		self.SetSizer(main)
		self.SetEscapeId(wx.ID_CLOSE)

		self.filterChoice.Bind(wx.EVT_CHOICE, self.onFilter)
		self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, lambda evt: self.activate())
		self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, lambda evt: self.updateButtons())
		self.tree.Bind(wx.EVT_TREE_KEY_DOWN, lambda evt: self.onKey(evt.GetKeyEvent()))
		# Enter, Delete and Alt+Shift+Arrows are caught before the dialog uses them
		# (in a dialog, Enter does not always reach the tree).
		self.Bind(wx.EVT_CHAR_HOOK, self.onCharHook)
		# The character of Enter must not reach the tree: its type-ahead search would move the selection.
		self.tree.Bind(wx.EVT_CHAR, lambda evt: None if evt.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) else evt.Skip())
		self.createButton.Bind(wx.EVT_BUTTON, self.onCreate)
		self.statusButton.Bind(wx.EVT_BUTTON, self.onStatus)
		self.moveButton.Bind(wx.EVT_BUTTON, self.onMove)
		self.deleteButton.Bind(wx.EVT_BUTTON, self.onDelete)
		self.searchButton.Bind(wx.EVT_BUTTON, self.onSearch)
		self.organizeButton.Bind(wx.EVT_BUTTON, self.onOrganize)
		self.closeButton.Bind(wx.EVT_BUTTON, lambda evt: self.Close())
		self.Bind(wx.EVT_CLOSE, self.onClose)

		self.refresh()
		main.Fit(self)
		self.CentreOnScreen()

	@property
	def store(self):
		return self.plugin.store

	def focusNotes(self):
		self.tree.SetFocus()

	# -- filters ------------------------------------------------------------------------------

	def filterLabel(self, flt):
		kind, ident = flt
		if kind == "loose":
			# Translators: filter: notes neither in a notebook nor in a folder.
			return _("Loose notes")
		if kind == "recent":
			# Translators: filter: the 10 notes changed last.
			return _("Recent notes")
		if kind == "notebook":
			# Translators: filter: the notes of a notebook.
			return _("Notebook: {name}").format(name=self.store.notebookName(ident))
		if kind == "folder":
			folder = self.store.getFolder(ident)
			# Translators: filter: the notes of a folder and of its notebooks.
			return _("Folder: {name}").format(name=folder["name"] if folder else "")
		# Translators: filter: every note.
		return _("All notes")

	def rebuildFilters(self):
		self.filters = [model.FILTER_ALL, model.FILTER_LOOSE, model.FILTER_RECENT]
		self.filters += [("notebook", nb["id"]) for nb in self.store.notebooks]
		self.filters += [("folder", f["id"]) for f in self.store.folders]
		if self.activeFilter not in self.filters:
			self.activeFilter = model.FILTER_ALL
		labels = [self.filterLabel(f) for f in self.filters]
		if labels != self.filterChoice.GetItems():
			self.filterChoice.SetItems(labels)
		self.filterChoice.SetSelection(self.filters.index(self.activeFilter))

	def setFilter(self, flt):
		self.activeFilter = flt
		self.shown = {}
		self.refresh()

	def onFilter(self, evt):
		self.setFilter(self.filters[max(0, self.filterChoice.GetSelection())])

	# -- content ------------------------------------------------------------------------------

	def _prepare(self, selectId):
		"""Notes of the filter by lane, the label with their number, and the pages that
		must be shown so that selectId is in the tree."""
		notes = self.store.filtered(self.activeFilter)
		lanes = model.byLane(notes)
		self.visibleIds = [n["id"] for lane in model.LANE_IDS for n in lanes[lane]]
		# Translators: label of the tree of notes: what it shows and how many.
		self.treeLabel.SetLabel(_("Not&es: {filter} ({count})").format(filter=escapeLabel(self.filterLabel(self.activeFilter)), count=len(notes)))
		for lane in model.LANE_IDS:
			shown = self.shown.get(lane, PAGE_SIZE)
			if selectId is not None:
				for i, note in enumerate(lanes[lane]):
					if note["id"] == selectId:
						if i >= shown:
							shown = (i // PAGE_SIZE + 1) * PAGE_SIZE
						break
			self.shown[lane] = shown
		return lanes

	def refresh(self, selectId=None, selectLane=None):
		"""Rebuilds the whole tree keeping (or choosing) the selection."""
		if self._closing:
			return
		self.rebuildFilters()
		lanes = self._prepare(selectId)
		self.tree.Freeze()
		try:
			self.fillTree(lanes, selectId, selectLane)
		finally:
			self.tree.Thaw()
		self.Layout()
		self.updateButtons()

	def refreshLanes(self, changed, selectId=None, selectLane=None):
		"""Rebuilds only some lanes (a status change touches two): fast with many notes."""
		if self._closing:
			return
		if not self.laneNodes or self.activeFilter == model.FILTER_RECENT:
			self.refresh(selectId, selectLane)
			return
		lanes = self._prepare(selectId)
		toSelect = None
		self.tree.Freeze()
		try:
			for lane in model.LANE_IDS:
				if lane not in changed:
					continue
				node = self.laneNodes[lane]
				for note in lanes[lane]:
					self.items.pop(note["id"], None)
				self.items = {k: v for k, v in self.items.items() if v.IsOk() and self.tree.GetItemParent(v) != node}
				self.tree.DeleteChildren(node)
				found = self.fillLane(node, lane, lanes[lane], selectId)
				toSelect = toSelect or found
				if lane == selectLane and selectId is None:
					toSelect = node
			if toSelect is None and selectId in self.items:
				toSelect = self.items[selectId]
			if toSelect is not None and toSelect.IsOk():
				selectItem(self.tree, toSelect)
		finally:
			self.tree.Thaw()
		self.updateButtons()

	def fillLane(self, node, lane, notes, selectId):
		"""Adds the shown page of a lane. Returns the item of selectId, if it is there."""
		tree = self.tree
		tree.SetItemText(node, messages.laneNode(lane, len(notes)))
		found = None
		shown = self.shown.get(lane, PAGE_SIZE)
		for note in notes[:shown]:
			child = tree.AppendItem(node, messages.noteDescription(note, messages.placeOf(self.store, note)), data={"note": note["id"]})
			self.items[note["id"]] = child
			if note["id"] == selectId:
				found = child
		if len(notes) > shown:
			tree.AppendItem(node, messages.moreNotes(len(notes) - shown, PAGE_SIZE), data={"more": lane})
		tree.Expand(node)
		return found

	def fillTree(self, lanes, selectId, selectLane):
		tree = self.tree
		tree.DeleteChildren(self.root)
		self.items = {}
		self.laneNodes = {}
		toSelect = None
		firstNode = None
		for lane in model.LANE_IDS:
			notes = lanes[lane]
			node = tree.AppendItem(self.root, "", data={"lane": lane})
			self.laneNodes[lane] = node
			firstNode = firstNode or node
			found = self.fillLane(node, lane, notes, selectId)
			toSelect = toSelect or found
			if lane == selectLane and selectId is None:
				toSelect = node
			if toSelect is None and selectId is None and selectLane is None and notes:
				toSelect = self.items.get(notes[0]["id"])
		toSelect = toSelect or firstNode
		if toSelect is not None:
			selectItem(tree, toSelect)

	def isShown(self, note):
		"""True when the note belongs to the filter shown."""
		if self.activeFilter == model.FILTER_RECENT:
			return note["id"] in [n["id"] for n in self.store.filtered(self.activeFilter)]
		return bool(model.filterNotes([note], self.store.notebooks, self.activeFilter))

	def noteChanged(self, noteId, fallback=None):
		"""After one note changed (title, tags, status, place or deleted): updates only what
		is needed. fallback: the note to select if this one left the list."""
		if self._closing:
			return
		note = self.store.getNote(noteId)
		item = self.items.get(noteId)
		if item is None or not item.IsOk():
			if note is not None and self.isShown(note):
				self.refreshLanes({note["laneId"]}, noteId)
			return
		oldLane = (self.tree.GetItemData(self.tree.GetItemParent(item)) or {}).get("lane")
		if note is None or not self.isShown(note):
			following = fallback or self.neighbourOf(noteId)
			self.refreshLanes({oldLane}, following, selectLane=oldLane if following is None else None)
		elif note["laneId"] != oldLane:
			self.refreshLanes({oldLane, note["laneId"]}, noteId)
		else:
			self.tree.SetItemText(item, messages.noteDescription(note, messages.placeOf(self.store, note)))
			self.updateButtons()

	def selectedData(self):
		item = self.tree.GetSelection()
		if not item.IsOk() or item == self.root:
			return {}
		return self.tree.GetItemData(item) or {}

	def selectedNoteId(self):
		return self.selectedData().get("note")

	def selectedLane(self):
		data = self.selectedData()
		note = self.store.getNote(data["note"]) if "note" in data else None
		if note:
			return note["laneId"]
		return data.get("lane") or data.get("more") or model.DEFAULT_LANE

	def updateButtons(self):
		# Also while Python ends: the tree may send events after the buttons are gone.
		if self._closing or not self.statusButton:
			return
		hasNote = self.selectedNoteId() is not None
		for button in (self.statusButton, self.moveButton, self.deleteButton):
			button.Enable(hasNote)

	def neighbourOf(self, noteId):
		"""The note that takes the place of noteId in the list (next, otherwise previous)."""
		ids = self.visibleIds
		if noteId not in ids:
			return None
		i = ids.index(noteId)
		if i + 1 < len(ids):
			return ids[i + 1]
		return ids[i - 1] if i > 0 else None

	def showMore(self, lane):
		"""Shows the next page of a lane, with the focus on its first new note."""
		lanes = model.byLane(self.store.filtered(self.activeFilter))
		first = self.shown.get(lane, PAGE_SIZE)
		self.shown[lane] = first + PAGE_SIZE
		ids = [n["id"] for n in lanes[lane]]
		self.refresh(ids[first] if first < len(ids) else None)

	# -- keyboard -------------------------------------------------------------------------------

	def onCharHook(self, evt):
		if self.FindFocus() is self.tree and self.handleTreeKey(evt):
			return
		evt.Skip()

	def onKey(self, evt):
		if not self.handleTreeKey(evt):
			evt.Skip()

	def handleTreeKey(self, evt):
		"""Enter opens, Delete deletes, Alt+Shift+Arrows change the status. True when handled."""
		key = evt.GetKeyCode()
		if key in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) and not evt.HasAnyModifiers():
			self.activate()
			return True
		if key in (wx.WXK_DELETE, wx.WXK_NUMPAD_DELETE) and not evt.HasAnyModifiers():
			self.onDelete(None)
			return True
		if evt.AltDown() and evt.ShiftDown() and not evt.ControlDown() and key in (wx.WXK_LEFT, wx.WXK_RIGHT):
			self.moveBy(1 if key == wx.WXK_RIGHT else -1)
			return True
		return False

	def activate(self):
		"""Enter or double click: opens the note, shows more notes or opens/closes the lane."""
		if self._pending:
			return
		data = self.selectedData()
		if "note" in data:
			self._pending = True
			wx.CallAfter(self.openNote, data["note"])
		elif "more" in data:
			self.showMore(data["more"])
		else:
			item = self.tree.GetSelection()
			if item.IsOk() and item != self.root:
				self.tree.Toggle(item)

	def openNote(self, noteId):
		try:
			if self._closing:
				return
			following = self.neighbourOf(noteId)
			self.plugin.editNote(self, noteId)
			if self._closing:
				return
			self.noteChanged(noteId, fallback=following)
			self.focusNotes()
		finally:
			self._pending = False

	# -- actions ----------------------------------------------------------------------------------

	def onCreate(self, evt):
		index = prompts.chooseFromMenu(self.createButton, messages.createLabels())
		kind, ident = self.activeFilter
		if index == 0:
			noteId = self.plugin.newNote(
				self,
				self.selectedLane(),
				ident if kind == "notebook" else None,
				ident if kind == "folder" else None,
			)
			if noteId:
				if noteId not in [n["id"] for n in self.store.filtered(self.activeFilter)]:
					self.activeFilter = model.FILTER_ALL
				self.refresh(noteId)
		elif index == 1:
			if self.plugin.createNotebook(self, ident if kind == "folder" else None):
				self.refresh(self.selectedNoteId())
		elif index == 2:
			if self.plugin.createFolder(self):
				self.refresh(self.selectedNoteId())
		self.focusNotes()

	def setStatus(self, noteId, laneId):
		ok, _changed = self.plugin.safe(self.store.moveNote, noteId, laneId)
		if ok:
			self.noteChanged(noteId)
			self.plugin.speak(messages.movedTo(laneId))
		self.focusNotes()

	def moveBy(self, step):
		noteId = self.selectedNoteId()
		if not noteId:
			return
		target = model.neighbourLane(self.store.getNote(noteId)["laneId"], step)
		if target is None:
			self.plugin.speak(messages.alreadyLast() if step > 0 else messages.alreadyFirst())
			return
		self.setStatus(noteId, target)

	def onStatus(self, evt):
		noteId = self.selectedNoteId()
		if not noteId:
			return
		current = self.store.getNote(noteId)["laneId"]
		others = [lane for lane in model.LANE_IDS if lane != current]
		index = prompts.chooseFromMenu(self.statusButton, [messages.laneName(lane) for lane in others])
		if index is None:
			self.focusNotes()
			return
		self.setStatus(noteId, others[index])

	def onMove(self, evt):
		noteId = self.selectedNoteId()
		if not noteId:
			return
		following = self.neighbourOf(noteId)
		if self.plugin.moveNote(self, self.store.getNote(noteId)):
			self.noteChanged(noteId, fallback=following)
		self.focusNotes()

	def onDelete(self, evt):
		noteId = self.selectedNoteId()
		if not noteId:
			return
		note = self.store.getNote(noteId)
		following = self.neighbourOf(noteId)
		if self.plugin.deleteNote(self, note):
			self.noteChanged(noteId, fallback=following)
		self.focusNotes()

	def onSearch(self, evt):
		openedId = self.plugin.openSearch(self)
		self.refresh(openedId or self.selectedNoteId())
		self.focusNotes()

	def onOrganize(self, evt):
		from .organizeDialog import OrganizeDialog

		dlg = OrganizeDialog(self, self.plugin)
		try:
			dlg.ShowModal()
		finally:
			if dlg:
				dlg.Destroy()
		self.refresh(self.selectedNoteId())
		self.focusNotes()

	def destroy(self):
		self._closing = True
		# Hidden first: deleting a long tree is faster when nothing is drawn.
		self.Hide()
		self.Destroy()

	def onClose(self, evt):
		"""Close (and Esc) only hide the window: building the tree again with many notes
		would take time. NVDA destroys it when the add-on ends."""
		if evt.CanVeto():
			self.Hide()
			return
		NotesDialog._instance = None
		self.destroy()
