# -*- coding: UTF-8 -*-
"""Starts wxPython with the NVDA fakes and loads the real add-on (its
__init__.py). Shared by the GUI test suites."""

import contextlib
import os
import sys
import time

import _helpers
import nvda_stubs
from nvda_stubs import RECORD

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_helpers.ROOT, "addon", "globalPlugins"))

nvda_stubs.install()
import wx  # noqa: E402

import gui  # noqa: E402  (fake)

app = wx.App(False)
# Without an active event loop, wx.Yield does not deliver timer events (the
# automatic saving and the search debounce); NVDA always has its main loop.
_loop = wx.GUIEventLoop()
wx.EventLoop.SetActive(_loop)
gui.mainFrame = gui.MainFrame()

import NotasWorkflowNVDA  # noqa: E402  (the real add-on)
from NotasWorkflowNVDA import mainDialog, markup, model, noteDialog, organizeDialog, prompts, searchDialog, settingsPanel, store  # noqa: E402

import config  # noqa: E402

MainDialog = mainDialog.NotesDialog


def pump(until=lambda: False, timeout=5.0):
	end = time.time() + timeout
	while time.time() < end:
		wx.Yield()
		if until():
			return True
		time.sleep(0.02)
	wx.Yield()
	return bool(until())


def spokenSince(n):
	return nvda_stubs.spoken()[n:]


def mark():
	return len(nvda_stubs.spoken())


def waitSpoken(n, predicate, timeout=3.0):
	return pump(lambda: any(predicate(s) for s in spokenSince(n)), timeout)


def newPlugin(folder=None):
	"""A fresh plugin (as when NVDA starts) with its own notes folder."""
	closeWindow()
	config.conf.spec[NotasWorkflowNVDA.CONFIG_SECTION] = NotasWorkflowNVDA.CONFIG_SPEC
	conf = config.conf[NotasWorkflowNVDA.CONFIG_SECTION]
	conf["dataFolder"] = folder or _helpers.tempFolder()
	conf["autoSaveSeconds"] = 1
	conf["announceAutoSave"] = False
	return NotasWorkflowNVDA.GlobalPlugin()


@contextlib.contextmanager
def fakeModal(cls, action):
	"""While active, cls.ShowModal() runs action(dialog) instead of a modal loop.
	EndModal(code) inside the action is recorded and returned by ShowModal."""
	names = ("ShowModal", "IsModal", "EndModal")
	# Methods inherited from wx must be removed, not set back (sip methods do not bind again).
	saved = {name: cls.__dict__.get(name) for name in names}

	def show(self):
		self._endCode = None
		result = action(self)
		if self._endCode is not None:
			return self._endCode
		return result if result is not None else wx.ID_CANCEL

	cls.ShowModal = show
	cls.IsModal = lambda self: True
	cls.EndModal = lambda self, code: setattr(self, "_endCode", code)
	try:
		yield
	finally:
		for name in names:
			if saved[name] is None:
				delattr(cls, name)
			else:
				setattr(cls, name, saved[name])


def newNoteAction(title, laneIndex=None, locationIndex=None):
	def action(dlg):
		dlg.titleEdit.SetValue(title)
		if laneIndex is not None:
			dlg.laneChoice.SetSelection(laneIndex)
		if locationIndex is not None:
			dlg.locationChoice.SetSelection(locationIndex)
		return wx.ID_OK if dlg.createButton.IsEnabled() else wx.ID_CANCEL
	return action


@contextlib.contextmanager
def creating(title, content=None, laneIndex=None, locationIndex=None):
	"""New note dialog filled with title; the note window types content and closes."""

	def edit(dlg):
		if content is not None:
			dlg.contentEdit.SetValue(content)
		dlg.finish()

	with fakeModal(noteDialog.NewNoteDialog, newNoteAction(title, laneIndex, locationIndex)), fakeModal(noteDialog.NoteDialog, edit):
		yield


@contextlib.contextmanager
def replaced(module, name, value):
	saved = getattr(module, name)
	setattr(module, name, value)
	try:
		yield
	finally:
		setattr(module, name, saved)


def menu(index):
	"""While active, every pop-up menu (Create, Update the task status) chooses item index."""
	return replaced(prompts, "chooseFromMenu", lambda window, labels: index)


def treeFind(tree, predicate, node=None):
	"""First item (depth first) whose data satisfies predicate."""
	node = node or tree.GetRootItem()
	child, cookie = tree.GetFirstChild(node)
	while child.IsOk():
		if predicate(tree.GetItemData(child) or {}):
			return child
		found = treeFind(tree, predicate, child)
		if found is not None:
			return found
		child, cookie = tree.GetNextChild(node, cookie)
	return None


def postKey(window, vk):
	"""A real key press through the Windows message queue (the path a keyboard takes, with
	the dialog and wx deciding who gets it), then the events are processed."""
	import ctypes

	window.SetFocus()
	pump(lambda: window.FindFocus() is window, 1)
	hwnd = ctypes.c_void_p(window.GetHandle())
	ctypes.windll.user32.PostMessageW(hwnd, 0x100, vk, 0)
	ctypes.windll.user32.PostMessageW(hwnd, 0x101, vk, 0xC0000001)
	pump(timeout=0.3)


VK_RETURN = 0x0D


def click(button):
	evt = wx.CommandEvent(wx.wxEVT_BUTTON, button.GetId())
	evt.SetEventObject(button)
	button.GetEventHandler().ProcessEvent(evt)


class Key:
	"""A key event for the handlers (onKey, onCharHook)."""

	def __init__(self, code, ctrl=False, alt=False, shift=False):
		self.code, self.ctrl, self.alt, self.shift = code, ctrl, alt, shift
		self.skipped = False

	def GetKeyCode(self):
		return self.code

	def ControlDown(self):
		return self.ctrl

	def AltDown(self):
		return self.alt

	def ShiftDown(self):
		return self.shift

	def HasAnyModifiers(self):
		return self.ctrl or self.alt or self.shift

	def Skip(self, skip=True):
		self.skipped = skip


def treeTexts(tree, node=None):
	"""[(text, [child texts])] of the top level of a tree."""
	out = []
	root = node or tree.GetRootItem()
	child, cookie = tree.GetFirstChild(root)
	while child.IsOk():
		kids = []
		sub, c2 = tree.GetFirstChild(child)
		while sub.IsOk():
			kids.append(tree.GetItemText(sub))
			sub, c2 = tree.GetNextChild(child, c2)
		out.append((tree.GetItemText(child), kids))
		child, cookie = tree.GetNextChild(root, cookie)
	return out


def tableRows(table):
	return [[table.GetItemText(r, c) for c in range(table.GetColumnCount())] for r in range(table.GetItemCount())]


def openWindow(plugin):
	plugin.openWindow()
	return MainDialog._instance


def closeWindow():
	if MainDialog._instance:
		MainDialog._instance.Close()
		pump(timeout=0.1)
