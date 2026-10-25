# -*- coding: UTF-8 -*-
# NotasWorkflowNVDA - locationTree.py
# The Location field of New note, of the note window and of Move to: a tree with
# loose, each folder (closed, its notebooks inside) and the notebooks without folder.
# Every item is a place: a folder itself means the note goes directly into it.
# Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
# This file is covered by the GNU General Public License, version 2.

import wx

from . import messages


class LocationTree(wx.TreeCtrl):
	"""The items follow messages.locationChoices: index i of the tree is places[i] and
	labels[i] (the label says the folder of a notebook, for what is spoken after a move).
	The folders start closed; only the folder of the chosen place opens."""

	def __init__(self, parent, store, size=(380, 150)):
		super().__init__(parent, size=size, style=wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS | wx.TR_LINES_AT_ROOT | wx.TR_SINGLE)
		self.labels, self.places = messages.locationChoices(store)
		self.items = []
		root = self.AddRoot("")
		folderItems = {}
		for index, (notebookId, folderId) in enumerate(self.places):
			parent = root
			if folderId is not None:
				folder = store.getFolder(folderId)
				text = messages.folderLocation(folder, len(store.notebooksIn(folderId)))
			elif notebookId is not None:
				nb = store.getNotebook(notebookId)
				text = messages.notebookPlace(nb)
				parent = folderItems.get(nb["folderId"], root)
			else:
				text = messages.looseNote()
			item = self.AppendItem(parent, text, data=index)
			if folderId is not None:
				folderItems[folderId] = item
			self.items.append(item)
		# The character of Enter must not reach the tree: its type-ahead search would move the selection.
		self.Bind(wx.EVT_CHAR, lambda evt: None if evt.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) else evt.Skip())
		self.setIndex(0)

	def index(self):
		item = self.GetSelection()
		if not item.IsOk():
			return 0
		index = self.GetItemData(item)
		return index if isinstance(index, int) else 0

	def setIndex(self, index):
		"""Selects a place (its folder opens) and makes it the focused item too: Windows keeps
		them apart, and when the tree gets the focus it would go back to the old one."""
		item = self.items[max(0, min(index, len(self.items) - 1))]
		self.SelectItem(item)
		self.SetFocusedItem(item)
		self.EnsureVisible(item)

	def place(self):
		"""(notebookId, folderId) of the chosen place."""
		return self.places[self.index()]

	def setPlace(self, place):
		self.setIndex(self.places.index(place) if place in self.places else 0)

	def label(self):
		return self.labels[self.index()]
