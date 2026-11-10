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
		#: Lanes the person opened. The lanes start closed (only the lane of a note being
		#: selected opens by itself), and stay as the person left them.
		self.expandedLanes = set()
		#: True while the window is being destroyed (deleting the tree still sends events).
		self._closing = False
		#: An Enter or a double click already asked to open something (avoids opening twice).
		self._pending = False
		#: (The window is kept hidden after Close; changes reach it the same way while hidden.)
		sHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		#: Show: a tree, as the Location tree: all, loose, recent, each folder (closed, its
		#: notebooks inside) and the notebooks without folder.
		self.filterTree = sHelper.addLabeledControl(
			# Translators: label of the tree that chooses which notes are shown.
			_("&Show:"),
			wx.TreeCtrl,
			size=(620, 130),
			style=wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS | wx.TR_LINES_AT_ROOT | wx.TR_SINGLE,
		)
		self.filterRoot = self.filterTree.AddRoot("")
		#: filter -> item of the Show tree, and what the tree was built from (rebuilt only when it changes).
		self.filterItems = {}
		self._filterShape = None
		#: True while the Show tree is being filled or selected by the window itself.
		self._fillingFilters = False
		self.treeLabel = wx.StaticText(self, label="")
		self.tree = wx.TreeCtrl(self, size=(620, 360), style=wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS | wx.TR_LINES_AT_ROOT | wx.TR_SINGLE)
		self.root = self.tree.AddRoot("")
		sHelper.addItem(self.treeLabel)
		sHelper.addItem(self.tree, flag=wx.EXPAND, proportion=1)

		actions = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: button that opens the menu to create a note, a notebook or a folder.
		self.createButton = actions.addButton(self, label=_("&Create…"))
		# The status, the place and the deletion of a note are done in the list (Alt+Shift+Arrows,
		# Delete) and in the note window: the window has no buttons for them (1.12.0).
		# Translators: button that opens the search window.
		self.searchButton = actions.addButton(self, label=_("Searc&h…"))
		# Translators: button that opens the window of notebooks and folders.
		self.organizeButton = actions.addButton(self, label=_("Notebooks and &folders…"))
		sHelper.addItem(actions)
		actions2 = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: button that opens the menu to export the selected note, a notebook or a folder.
		self.exportButton = actions2.addButton(self, label=_("E&xport…"))
		# Translators: button that opens the user manual of the add-on.
		self.manualButton = actions2.addButton(self, label=_("User ma&nual…"))
		# Translators: button that closes the window.
		self.closeButton = actions2.addButton(self, id=wx.ID_CLOSE, label=_("C&lose"))
		sHelper.addItem(actions2)

		main = wx.BoxSizer(wx.VERTICAL)
		main.Add(sHelper.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL | wx.EXPAND, proportion=1)
		self.SetSizer(main)
		self.SetEscapeId(wx.ID_CLOSE)

		self.filterTree.Bind(wx.EVT_TREE_SEL_CHANGED, self.onFilter)
		# Enter (or a double click) in Show goes to the notes; its character must not reach the
		# tree: its type-ahead search would move the selection.
		self.filterTree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, lambda evt: self.focusNotes())
		self.filterTree.Bind(wx.EVT_CHAR, lambda evt: None if evt.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) else evt.Skip())
		self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, lambda evt: self.activate())
		self.tree.Bind(wx.EVT_TREE_ITEM_EXPANDED, lambda evt: self.onLaneOpened(evt, True))
		self.tree.Bind(wx.EVT_TREE_ITEM_COLLAPSED, lambda evt: self.onLaneOpened(evt, False))
		self.tree.Bind(wx.EVT_TREE_KEY_DOWN, lambda evt: self.onKey(evt.GetKeyEvent()))
		# Enter, Delete, Alt+Shift+Arrows and Ctrl+Shift+Arrows are caught before the dialog uses them
		# (in a dialog, Enter does not always reach the tree).
		self.Bind(wx.EVT_CHAR_HOOK, self.onCharHook)
		# The character of Enter must not reach the tree: its type-ahead search would move the selection.
		self.tree.Bind(wx.EVT_CHAR, lambda evt: None if evt.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) else evt.Skip())
		self.createButton.Bind(wx.EVT_BUTTON, self.onCreate)
		self.searchButton.Bind(wx.EVT_BUTTON, self.onSearch)
		self.organizeButton.Bind(wx.EVT_BUTTON, self.onOrganize)
		self.exportButton.Bind(wx.EVT_BUTTON, self.onExport)
		self.manualButton.Bind(wx.EVT_BUTTON, lambda evt: self.plugin.openManual())
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

	def filterShape(self):
		"""[(filter, parent filter or None)] in the order of the Show tree: all, loose, recent,
		each folder followed by its notebooks, then the notebooks without folder."""
		shape = [(model.FILTER_ALL, None), (model.FILTER_LOOSE, None), (model.FILTER_RECENT, None)]
		for folder in self.store.folders:
			flt = ("folder", folder["id"])
			shape.append((flt, None))
			shape += [(("notebook", nb["id"]), flt) for nb in self.store.notebooksIn(folder["id"])]
		shape += [(("notebook", nb["id"]), None) for nb in self.store.notebooksIn(None)]
		return shape

	def filterLabels(self):
		"""Texts of the Show tree, in its order (items inside a folder included)."""
		return [self.filterTree.GetItemText(self.filterItems[flt]) for flt in self.filters]

	def rebuildFilters(self):
		"""Builds the Show tree again only when its folders, notebooks or names changed; then
		selects the filter shown (its folder opens)."""
		shape = self.filterShape()
		self.filters = [flt for flt, _parent in shape]
		if self.activeFilter not in self.filters:
			self.activeFilter = model.FILTER_ALL
		labels = [self.filterLabel(flt) for flt in self.filters]
		tree = self.filterTree
		self._fillingFilters = True
		try:
			if (shape, labels) != self._filterShape:
				tree.Freeze()
				try:
					tree.DeleteChildren(self.filterRoot)
					self.filterItems = {}
					for (flt, parent), label in zip(shape, labels):
						owner = self.filterItems.get(parent, self.filterRoot)
						self.filterItems[flt] = tree.AppendItem(owner, label, data=flt)
				finally:
					tree.Thaw()
				self._filterShape = (shape, labels)
			item = self.filterItems[self.activeFilter]
			if tree.GetSelection() != item:
				selectItem(tree, item)
		finally:
			self._fillingFilters = False

	def setFilter(self, flt):
		self.activeFilter = flt
		self.shown = {}
		self.refresh()

	def onFilter(self, evt):
		"""An item of Show was selected (arrows, mouse): its notes are shown."""
		if self._closing or self._fillingFilters:
			return
		item = self.filterTree.GetSelection()
		flt = self.filterTree.GetItemData(item) if item.IsOk() else None
		if flt in self.filters and flt != self.activeFilter:
			self.setFilter(flt)

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
		if lane in self.expandedLanes:
			tree.Expand(node)
		return found

	def onLaneOpened(self, evt, opened):
		"""Remembers which lanes the person opened (selecting a note also opens its lane)."""
		if self._closing:
			return
		data = self.tree.GetItemData(evt.GetItem()) or {}
		if "lane" in data:
			if opened:
				self.expandedLanes.add(data["lane"])
			else:
				self.expandedLanes.discard(data["lane"])
		evt.Skip()

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
		# Without a note to select, the focus is on the first lane (all lanes closed).
		toSelect = toSelect or firstNode
		if toSelect is not None:
			selectItem(tree, toSelect)

	def isShown(self, note):
		"""True when the note belongs to the filter shown."""
		if self.activeFilter == model.FILTER_RECENT:
			return note["id"] in [n["id"] for n in self.store.filtered(self.activeFilter)]
		return bool(model.filterNotes([note], self.store.notebooks, self.activeFilter))

	def noteChanged(self, noteId, fallback=None):
		"""After one note changed (title, status, place or deleted): updates only what
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

	def neighbourOf(self, noteId):
		"""The note that takes the place of noteId in the list (next, otherwise previous)."""
		ids = self.visibleIds
		if noteId not in ids:
			return None
		i = ids.index(noteId)
		if i + 1 < len(ids):
			return ids[i + 1]
		return ids[i - 1] if i > 0 else None

	def nextInLane(self, noteId):
		"""The note after noteId in its lane (the next one in the pile), otherwise the one
		before it, or None when it is alone in the lane."""
		note = self.store.getNote(noteId)
		if note is None:
			return None
		ids = [n["id"] for n in model.byLane(self.store.filtered(self.activeFilter))[note["laneId"]]]
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
		"""Enter opens, Delete deletes, Alt+Shift+Left/Right change the status, Ctrl+Shift+Up/Down
		move the note in its lane. True when handled."""
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
		if evt.ControlDown() and evt.ShiftDown() and not evt.AltDown() and key in (wx.WXK_UP, wx.WXK_DOWN):
			self.reorder(1 if key == wx.WXK_DOWN else -1)
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
			before = self.store.getNote(noteId)
			lane = before["laneId"] if before else None
			following = self.nextInLane(noteId)
			self.plugin.editNote(self, noteId)
			if self._closing:
				return
			after = self.store.getNote(noteId)
			if after is not None and after["laneId"] == lane and self.isShown(after):
				# Still in the same place of the pile: the focus comes back to it.
				self.noteChanged(noteId)
				if noteId in self.items:
					selectItem(self.tree, self.items[noteId])
			else:
				# Moved to another status (or out of what is shown): the focus goes to the
				# next note of the pile it was in (the previous one if it was the last).
				changed = {lane} | ({after["laneId"]} if after else set())
				self.refreshLanes(changed, following, selectLane=lane if following is None else None)
			self.focusNotes()
		finally:
			self._pending = False

	# -- actions ----------------------------------------------------------------------------------

	def onCreate(self, evt):
		index = prompts.chooseFromMenu(self.createButton, messages.createLabels())
		kind, ident = self.activeFilter
		where = (self.selectedLane(), ident if kind == "notebook" else None, ident if kind == "folder" else None)
		if index == 0:
			self.noteCreated(self.plugin.newNote(self, *where))
		elif index == 3:
			# The document is read in the background: the note comes later.
			if self.plugin.noteFromDocument(self, *where, done=self.noteCreated):
				return
		elif index == 1:
			if self.plugin.createNotebook(self, ident if kind == "folder" else None):
				self.refresh(self.selectedNoteId())
		elif index == 2:
			if self.plugin.createFolder(self):
				self.refresh(self.selectedNoteId())
		self.focusNotes()

	def noteCreated(self, noteId):
		"""Shows a new note selected (all notes, if the filter shown leaves it out)."""
		if self._closing:
			return
		if noteId:
			if noteId not in [n["id"] for n in self.store.filtered(self.activeFilter)]:
				self.activeFilter = model.FILTER_ALL
			self.refresh(noteId)
		else:
			# New note may have created a notebook or a folder before being cancelled: Show
			# gets it (the tree of notes did not change).
			self.rebuildFilters()
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

	def reorder(self, step):
		"""Ctrl+Shift+Up (step -1) or Down (+1): the note goes up or down in its lane, past the
		note shown next to it. Only the two items of the tree change places."""
		noteId = self.selectedNoteId()
		if not noteId:
			return
		if self.activeFilter == model.FILTER_RECENT:
			self.plugin.speak(messages.noOrderInRecent())
			return
		note = self.store.getNote(noteId)
		ids = [n["id"] for n in model.byLane(self.store.filtered(self.activeFilter))[note["laneId"]]]
		i = ids.index(noteId)
		j = i + step
		if not 0 <= j < len(ids):
			self.plugin.speak(messages.alreadyBottom() if step > 0 else messages.alreadyTop())
			return
		otherId = ids[j]
		ok, changed = self.plugin.safe(self.store.placeNoteBeside, noteId, otherId, step > 0)
		if not ok or not changed:
			return
		item, otherItem = self.items.get(noteId), self.items.get(otherId)
		if item is not None and otherItem is not None and item.IsOk() and otherItem.IsOk():
			tree = self.tree
			text, otherText = tree.GetItemText(item), tree.GetItemText(otherItem)
			tree.SetItemText(item, otherText)
			tree.SetItemData(item, {"note": otherId})
			tree.SetItemText(otherItem, text)
			tree.SetItemData(otherItem, {"note": noteId})
			self.items[noteId], self.items[otherId] = otherItem, item
			a, b = self.visibleIds.index(noteId), self.visibleIds.index(otherId)
			self.visibleIds[a], self.visibleIds[b] = otherId, noteId
			selectItem(tree, otherItem)
		else:
			# The other note is in a page not shown yet.
			self.refreshLanes({note["laneId"]}, noteId)
		self.plugin.speak(messages.positionInLane(j + 1, len(ids)))
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

	def onExport(self, evt):
		"""Export…: the selected note, a notebook or a folder (the one shown, or the one of the
		selected note, comes chosen)."""
		noteId = self.selectedNoteId()
		labels = messages.exportLabels(noteId is not None)
		index = prompts.chooseFromMenu(self.exportButton, labels)
		if index is None:
			self.focusNotes()
			return
		if noteId is None:
			index += 1
		if index == 0:
			self.plugin.exportItem(self, "note", noteId)
		else:
			ident = self.chooseExported("notebook" if index == 1 else "folder")
			if ident is not None:
				self.plugin.exportItem(self, "notebook" if index == 1 else "folder", ident)
		self.focusNotes()

	def chooseExported(self, kind):
		"""Asks which notebook or folder to export; id or None."""
		kindShown, shown = self.activeFilter
		note = self.store.getNote(self.selectedNoteId()) if self.selectedNoteId() else None
		if kind == "notebook":
			items = self.store.notebooks
			labels = [messages.notebookPlace(nb, self.store.getFolder(nb["folderId"])) for nb in items]
			current = shown if kindShown == "notebook" else (note["notebookId"] if note else None)
			# Translators: question of the dialog that chooses the notebook to export.
			question = _("Export which notebook?")
		else:
			items = self.store.folders
			labels = [messages.folderPlace(f) for f in items]
			current = shown if kindShown == "folder" else None
			if current is None and note:
				nb = self.store.getNotebook(note["notebookId"]) if note["notebookId"] else None
				current = nb["folderId"] if nb else note["folderId"]
			# Translators: question of the dialog that chooses the folder to export.
			question = _("Export which folder?")
		if not items:
			if kind == "notebook":
				# Translators: spoken when Export > Notebook is chosen and there is no notebook.
				self.plugin.speak(_("There are no notebooks."))
			else:
				# Translators: spoken when Export > Folder is chosen and there is no folder.
				self.plugin.speak(_("There are no folders."))
			return None
		ids = [item["id"] for item in items]
		# Translators: title of the dialogs that export notes.
		index = prompts.chooseItem(self, question, _("Export"), labels, ids.index(current) if current in ids else 0)
		return None if index is None else ids[index]

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
