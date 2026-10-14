# -*- coding: UTF-8 -*-
# NotasWorkflowNVDA - prompts.py
# Small dialogs and menus shared by the windows. They are module functions so the
# tests can replace them (a real menu or modal dialog would wait for the user).
# Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
# This file is covered by the GNU General Public License, version 2.

import wx

from . import model


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
