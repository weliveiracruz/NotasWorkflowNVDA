# -*- coding: UTF-8 -*-
# NotasWorkflowNVDA - prompts.py
# Small dialogs and menus shared by the windows. They are module functions so the
# tests can replace them (a real menu or modal dialog would wait for the user).
# Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
# This file is covered by the GNU General Public License, version 2.

import addonHandler
import wx
from gui import guiHelper

from . import model
from .locationTree import LocationTree

addonHandler.initTranslation()


def chooseFromMenu(window, labels):
	"""Shows a pop-up menu with the labels and returns the chosen index, or None."""
	menu = wx.Menu()
	ids = {}
	for index, label in enumerate(labels):
		item = menu.Append(wx.ID_ANY, label)
		ids[item.GetId()] = index
	chosen = []
	menu.Bind(wx.EVT_MENU, lambda evt: chosen.append(ids.get(evt.GetId())))
	window.PopupMenu(menu)
	menu.Destroy()
	return chosen[0] if chosen else None


def chooseItem(parent, message, caption, labels, current=0):
	"""Index chosen in a list dialog, or None."""
	dlg = wx.SingleChoiceDialog(parent, message, caption, labels)
	try:
		if labels:
			dlg.SetSelection(max(0, min(current, len(labels) - 1)))
		if dlg.ShowModal() != wx.ID_OK:
			return None
		return dlg.GetSelection()
	finally:
		dlg.Destroy()


class PlaceDialog(wx.Dialog):
	"""A Location tree, OK and Cancel; Enter in the tree is OK. The title says what is moved."""

	def __init__(self, parent, caption, store, current=0):
		super().__init__(parent, title=caption)
		sHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		# Translators: label of the tree with the place of a note: loose, a folder or a notebook (inside its folder).
		self.tree = sHelper.addLabeledControl(_("&Location:"), LocationTree, store=store)
		self.tree.setIndex(current)
		buttons = guiHelper.ButtonHelper(wx.HORIZONTAL)
		self.okButton = buttons.addButton(self, id=wx.ID_OK)
		self.cancelButton = buttons.addButton(self, id=wx.ID_CANCEL)
		sHelper.addItem(buttons, flag=wx.ALIGN_RIGHT)
		main = wx.BoxSizer(wx.VERTICAL)
		main.Add(sHelper.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL | wx.EXPAND)
		self.SetSizer(main)
		main.Fit(self)
		self.okButton.SetDefault()
		self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, lambda evt: self.EndModal(wx.ID_OK))
		self.CentreOnScreen()
		self.tree.SetFocus()


def choosePlace(parent, caption, store, current=0):
	"""Index (as in messages.locationChoices) of the place chosen in a Location tree, or None."""
	dlg = PlaceDialog(parent, caption, store, current)
	try:
		if dlg.ShowModal() != wx.ID_OK:
			return None
		return dlg.tree.index()
	finally:
		dlg.Destroy()


def askSaveFile(parent, title, defaultFile, wildcard):
	"""Path of a new file chosen by the person (asks before replacing one), or None."""
	dlg = wx.FileDialog(parent, title, defaultFile=defaultFile, wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
	try:
		return dlg.GetPath() if dlg.ShowModal() == wx.ID_OK else None
	finally:
		dlg.Destroy()


def askFolder(parent, message):
	"""Folder chosen by the person, or None."""
	dlg = wx.DirDialog(parent, message, "", wx.DD_DEFAULT_STYLE)
	try:
		return dlg.GetPath() if dlg.ShowModal() == wx.ID_OK else None
	finally:
		dlg.Destroy()


def askText(parent, message, caption, value="", maxLength=model.MAX_NAME):
	"""Text typed in a dialog, or None when cancelled."""
	dlg = wx.TextEntryDialog(parent, message, caption, value)
	try:
		dlg.SetMaxLength(maxLength)
		if dlg.ShowModal() != wx.ID_OK:
			return None
		return dlg.GetValue()
	finally:
		dlg.Destroy()
