# -*- coding: UTF-8 -*-
# NotasWorkflowNVDA - organizeDialog.py
# "Notebooks and folders": a tree with each folder, its notebooks and the notes of
# each one, plus the notebooks without folder and the loose notes. Notes are
# loaded only when their branch is opened, in pages, so the window stays fast
# with 100,000 notes. Enter opens a note.
# Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
# This file is covered by the GNU General Public License, version 2.

import addonHandler
import gui
import wx
from gui import guiHelper

from . import messages, model, prompts
from .mainDialog import selectItem

addonHandler.initTranslation()

#: Notes added to a branch at a time; "Show more notes" adds the next page.
PAGE_SIZE = 200


class OrganizeDialog(wx.Dialog):
	def __init__(self, parent, plugin):
		# Translators: title of the window of notebooks and folders.
		super().__init__(parent, title=_("Notebooks and folders"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		self.plugin = plugin
		#: key -> tree item of what is in the tree now.
		self.nodes = {}
		#: Notes shown in each branch (pages of PAGE_SIZE) and branches whose notes were added.
		self.shown = {}
		self.loaded = set()
		self._pending = False
		self._closing = False
		sHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		# Translators: label of the tree of folders, notebooks and notes.
		self.treeLabel = wx.StaticText(self, label=_("&Organization:"))
		self.tree = wx.TreeCtrl(self, size=(520, 340), style=wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS | wx.TR_LINES_AT_ROOT | wx.TR_SINGLE)
		self.root = self.tree.AddRoot("")
		sHelper.addItem(self.treeLabel)
		sHelper.addItem(self.tree, flag=wx.EXPAND, proportion=1)
		buttons = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: button that opens the menu to create a note, a notebook or a folder.
		self.createButton = buttons.addButton(self, label=_("&Create…"))
		# Translators: button that renames the selected folder or notebook, or changes the title of the selected note.
		self.renameButton = buttons.addButton(self, label=_("&Rename…"))
		# Translators: button that moves the selected notebook to a folder, or the selected note to a notebook or folder.
		self.moveButton = buttons.addButton(self, label=_("&Move to…"))
		# Translators: button that deletes the selected folder, notebook or note.
		self.deleteButton = buttons.addButton(self, label=_("&Delete"))
		# Translators: button that closes the window.
		self.closeButton = buttons.addButton(self, id=wx.ID_CLOSE, label=_("C&lose"))
		sHelper.addItem(buttons)
		main = wx.BoxSizer(wx.VERTICAL)
		main.Add(sHelper.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL | wx.EXPAND, proportion=1)
		self.SetSizer(main)
		main.Fit(self)
		self.SetEscapeId(wx.ID_CLOSE)
		self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, lambda evt: self.updateButtons())
		self.tree.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.onExpanding)
		self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, lambda evt: self.activate())
		self.tree.Bind(wx.EVT_TREE_KEY_DOWN, lambda evt: self.onKey(evt.GetKeyEvent()))
		self.Bind(wx.EVT_CHAR_HOOK, self.onCharHook)
		# The character of Enter must not reach the tree: its type-ahead search would move the selection.
		self.tree.Bind(wx.EVT_CHAR, lambda evt: None if evt.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) else evt.Skip())
		self.createButton.Bind(wx.EVT_BUTTON, self.onCreate)
		self.renameButton.Bind(wx.EVT_BUTTON, self.onRename)
		self.moveButton.Bind(wx.EVT_BUTTON, self.onMove)
		self.deleteButton.Bind(wx.EVT_BUTTON, self.onDelete)
		self.closeButton.Bind(wx.EVT_BUTTON, lambda evt: self.close())
		self.Bind(wx.EVT_CLOSE, lambda evt: self.close())
		self.refresh()
		self.CentreOnScreen()
		self.tree.SetFocus()

	@property
	def store(self):
		return self.plugin.store

	# -- tree -------------------------------------------------------------------------------------

	def branchNotes(self, key):
		kind, ident = key
		if kind == "notebook":
			return self.store.notesIn(ident)
		if kind == "folder":
			return self.store.notesInFolder(ident)
		if kind == "loose":
			return self.store.looseNotes()
		return []

	def _add(self, parent, key, text):
		node = self.tree.AppendItem(parent, text, data={"key": key})
		self.nodes[key] = node
		return node

	def refresh(self, select=None):
		"""Rebuilds the tree, keeping the open branches. select: a key such as
		("folder", id), ("notebook", id) or ("note", id); None keeps the selection."""
		if self._closing:
			return
		select = select or self.selectedKey()
		expanded = [key for key, node in self.nodes.items() if node.IsOk() and key[0] != "note" and self.tree.IsExpanded(node)]
		tree = self.tree
		tree.Freeze()
		try:
			tree.DeleteChildren(self.root)
			self.nodes = {}
			self.loaded = set()
			self.counts = self.store.placeCounts()
			byFolder = self.counts[1]
			for folder in self.store.folders:
				notebooks = self.store.notebooksIn(folder["id"])
				direct = byFolder.get(folder["id"], 0)
				# Translators: a folder in the tree: name, number of notebooks and number of notes put directly in it.
				text = _("Folder {name}, {notebooks}, {notes}").format(name=folder["name"], notebooks=messages.notebooksCount(len(notebooks)), notes=messages.notesCount(direct))
				node = self._add(self.root, ("folder", folder["id"]), text)
				for nb in notebooks:
					self.addNotebook(node, nb)
				tree.SetItemHasChildren(node, bool(notebooks or direct))
			loose = self.store.notebooksIn(None)
			# Translators: branch of the tree with the notebooks that are not in a folder.
			node = self._add(self.root, ("none", None), _("Without folder, {count}").format(count=messages.notebooksCount(len(loose))))
			for nb in loose:
				self.addNotebook(node, nb)
			tree.SetItemHasChildren(node, bool(loose))
			looseCount = self.counts[2]
			# Translators: branch of the tree with the notes that are neither in a notebook nor in a folder.
			node = self._add(self.root, ("loose", None), _("Loose notes, {count}").format(count=messages.notesCount(looseCount)))
			tree.SetItemHasChildren(node, looseCount > 0)
			if select and select[0] == "note":
				note = self.store.getNote(select[1])
				if note:
					expanded.append(self.branchOf(note))
			for key in expanded:
				self.expandKey(key)
			node = self.nodes.get(select) if select else None
			if node is None or not node.IsOk():
				node, _cookie = tree.GetFirstChild(self.root)
			if node.IsOk():
				selectItem(tree, node)
		finally:
			tree.Thaw()
		self.updateButtons()

	def addNotebook(self, parent, nb):
		count = self.counts[0].get(nb["id"], 0)
		node = self._add(parent, ("notebook", nb["id"]), "%s, %s" % (nb["name"], messages.notesCount(count)))
		self.tree.SetItemHasChildren(node, count > 0)

	def branchOf(self, note):
		if note["notebookId"]:
			return ("notebook", note["notebookId"])
		if note["folderId"]:
			return ("folder", note["folderId"])
		return ("loose", None)

	def expandKey(self, key):
		"""Opens a branch (and the folder of a notebook), making sure its notes are there."""
		if key[0] == "notebook":
			nb = self.store.getNotebook(key[1])
			if nb:
				self.expandKey(("folder", nb["folderId"]) if nb["folderId"] else ("none", None))
		node = self.nodes.get(key)
		if node is None or not node.IsOk():
			return
		self.loadNotes(key)
		self.tree.Expand(node)

	def onExpanding(self, evt):
		data = self.tree.GetItemData(evt.GetItem()) or {}
		if "key" in data:
			self.loadNotes(data["key"])
		evt.Skip()

	def loadNotes(self, key, until=None):
		"""Adds the notes of a branch (the first page, or up to the page of note `until`)."""
		if key[0] not in ("notebook", "folder", "loose") or key in self.loaded:
			return
		self.loaded.add(key)
		notes = self.branchNotes(key)
		shown = self.shown.get(key, PAGE_SIZE)
		ids = [n["id"] for n in notes]
		if until in ids and ids.index(until) >= shown:
			shown = (ids.index(until) // PAGE_SIZE + 1) * PAGE_SIZE
		self.shown[key] = shown
		parent = self.nodes[key]
		for note in notes[:shown]:
			self._add(parent, ("note", note["id"]), messages.noteDescription(note, "", withLane=True))
		if len(notes) > shown:
			self._add(parent, ("more", key), messages.moreNotes(len(notes) - shown, PAGE_SIZE))

	def selectedKey(self):
		item = self.tree.GetSelection()
		if not item.IsOk() or item == self.root:
			return None
		return (self.tree.GetItemData(item) or {}).get("key")

	def selected(self):
		"""(kind, id) of the selection: folder, notebook, note, none, loose, more, or (None, None)."""
		return self.selectedKey() or (None, None)

	def updateButtons(self):
		if self._closing or not self.tree:
			return
		kind, ident = self.selected()
		self.renameButton.Enable(kind in ("folder", "notebook", "note"))
		self.deleteButton.Enable(kind in ("folder", "notebook", "note"))
		self.moveButton.Enable(kind == "note" or (kind == "notebook" and bool(self.store.folders)))

	def place(self):
		"""(notebookId, folderId) where a new note goes, from the selection."""
		kind, ident = self.selected()
		if kind == "notebook":
			return ident, None
		if kind == "folder":
			return None, ident
		if kind == "note":
			note = self.store.getNote(ident)
			return (note["notebookId"], note["folderId"]) if note else (None, None)
		return None, None

	def targetFolder(self):
		kind, ident = self.selected()
		if kind == "folder":
			return ident
		notebookId, folderId = self.place()
		if notebookId:
			return self.store.getNotebook(notebookId)["folderId"]
		return folderId

	# -- keyboard -------------------------------------------------------------------------------------

	def onCharHook(self, evt):
		if self.FindFocus() is self.tree and self.handleTreeKey(evt):
			return
		evt.Skip()

	def onKey(self, evt):
		if not self.handleTreeKey(evt):
			evt.Skip()

	def handleTreeKey(self, evt):
		key = evt.GetKeyCode()
		if evt.HasAnyModifiers():
			return False
		if key in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
			self.activate()
			return True
		if key in (wx.WXK_DELETE, wx.WXK_NUMPAD_DELETE):
			self.onDelete(None)
			return True
		if key == wx.WXK_F2:
			self.onRename(None)
			return True
		return False

	def activate(self):
		"""Enter or double click: opens the note, shows more notes or opens/closes the branch."""
		if self._pending:
			return
		kind, ident = self.selected()
		if kind == "note":
			self._pending = True
			wx.CallAfter(self.openNote, ident)
		elif kind == "more":
			self.showMore(ident)
		else:
			item = self.tree.GetSelection()
			if item.IsOk() and item != self.root:
				self.tree.Toggle(item)

	def openNote(self, noteId):
		try:
			if self._closing:
				return
			self.plugin.editNote(self, noteId)
			if self._closing:
				return
			self.refresh(("note", noteId) if self.store.getNote(noteId) else None)
			self.tree.SetFocus()
		finally:
			self._pending = False

	def showMore(self, key):
		notes = self.branchNotes(key)
		first = self.shown.get(key, PAGE_SIZE)
		self.shown[key] = first + PAGE_SIZE
		self.refresh(("note", notes[first]["id"]) if first < len(notes) else key)

	# -- actions ---------------------------------------------------------------------------------------

	def onCreate(self, evt):
		index = prompts.chooseFromMenu(self.createButton, messages.createLabels())
		if index == 0:
			notebookId, folderId = self.place()
			noteId = self.plugin.newNote(self, model.DEFAULT_LANE, notebookId, folderId)
			if noteId:
				self.refresh(("note", noteId))
		elif index == 3:
			notebookId, folderId = self.place()
			# The document is read in the background: the note comes later.
			if self.plugin.noteFromDocument(self, model.DEFAULT_LANE, notebookId, folderId, done=self.noteCreated):
				return
		elif index == 1:
			notebook = self.plugin.createNotebook(self, self.targetFolder())
			if notebook:
				self.refresh(("notebook", notebook["id"]))
		elif index == 2:
			folder = self.plugin.createFolder(self)
			if folder:
				self.refresh(("folder", folder["id"]))
		self.tree.SetFocus()

	def noteCreated(self, noteId):
		# The window may have been closed while the document was read.
		if not self:
			return
		if noteId:
			self.refresh(("note", noteId))
		self.tree.SetFocus()

	def onRename(self, evt):
		kind, ident = self.selected()
		if kind == "note":
			note = self.store.getNote(ident)
			# Translators: question and title of the dialog that changes the title of a note.
			title = prompts.askText(self, _("New title:"), _("Rename"), note["title"], model.MAX_TITLE)
			if title is not None and title.strip() and title.strip() != note["title"]:
				ok, _r = self.plugin.safe(self.store.updateNote, ident, title=title)
				if ok:
					self.refresh(("note", ident))
					# Translators: spoken after renaming a notebook, a folder or a note.
					self.plugin.speak(_("Renamed to {name}").format(name=note["title"]))
			self.tree.SetFocus()
			return
		if kind not in ("folder", "notebook"):
			return
		item = self.store.getFolder(ident) if kind == "folder" else self.store.getNotebook(ident)
		# Translators: question and title of the dialog that renames a notebook or folder.
		name = prompts.askText(self, _("New name:"), _("Rename"), item["name"])
		if name is None or not name.strip() or name.strip() == item["name"]:
			self.tree.SetFocus()
			return
		func = self.store.renameFolder if kind == "folder" else self.store.renameNotebook
		ok, _r = self.plugin.safe(func, ident, name)
		if ok:
			self.refresh((kind, ident))
			# Translators: spoken after renaming a notebook, a folder or a note.
			self.plugin.speak(_("Renamed to {name}").format(name=item["name"]))
		self.tree.SetFocus()

	def onMove(self, evt):
		kind, ident = self.selected()
		if kind == "note":
			if self.plugin.moveNote(self, self.store.getNote(ident)):
				self.refresh(("note", ident))
			self.tree.SetFocus()
			return
		if kind != "notebook":
			return
		notebook = self.store.getNotebook(ident)
		# Translators: option of the dialog that moves a notebook: no folder.
		labels = [_("Without folder")] + [f["name"] for f in self.store.folders]
		ids = [None] + [f["id"] for f in self.store.folders]
		index = prompts.chooseItem(
			self,
			# Translators: question of the dialog that moves a notebook to a folder.
			_("Folder of the notebook {name}:").format(name=notebook["name"]),
			# Translators: title of the dialog that moves a notebook to a folder.
			_("Move to folder"),
			labels,
			ids.index(notebook["folderId"]) if notebook["folderId"] in ids else 0,
		)
		if index is None or ids[index] == notebook["folderId"]:
			self.tree.SetFocus()
			return
		ok, _r = self.plugin.safe(self.store.moveNotebookToFolder, ident, ids[index])
		if ok:
			self.refresh(("notebook", ident))
			self.plugin.speak(messages.movedToPlace(labels[index]))
		self.tree.SetFocus()

	def onDelete(self, evt):
		kind, ident = self.selected()
		if kind == "note":
			note = self.store.getNote(ident)
			branch = self.branchOf(note)
			if self.plugin.deleteNote(self, note):
				self.refresh(branch)
			self.tree.SetFocus()
			return
		if kind not in ("folder", "notebook"):
			return
		if kind == "folder":
			item = self.store.getFolder(ident)
			# Translators: confirmation before deleting a folder.
			question = _("Delete the folder {name}? Its notebooks and notes are not deleted: they stay without folder.").format(name=item["name"])
		else:
			item = self.store.getNotebook(ident)
			# Translators: confirmation before deleting a notebook.
			question = _("Delete the notebook {name}? Its notes are not deleted: they become loose notes.").format(name=item["name"])
		# Translators: title of the confirmation before deleting a notebook or folder.
		answer = gui.messageBox(question, _("Delete"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING, self)
		if answer != wx.YES:
			self.tree.SetFocus()
			return
		func = self.store.deleteFolder if kind == "folder" else self.store.deleteNotebook
		ok, _r = self.plugin.safe(func, ident)
		if ok:
			self.nodes.pop((kind, ident), None)
			self.refresh(("none", None))
			# Translators: spoken after a notebook or folder is deleted.
			self.plugin.speak(_("{name} deleted").format(name=item["name"]))
		self.tree.SetFocus()

	def close(self):
		self._closing = True
		if self.IsModal():
			self.EndModal(wx.ID_CLOSE)
		else:
			self.Destroy()
