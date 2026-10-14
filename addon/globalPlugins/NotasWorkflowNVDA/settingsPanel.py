# -*- coding: UTF-8 -*-
# NotasWorkflowNVDA - settingsPanel.py
# NVDA settings > Notas Workflow NVDA: where the notes
# are stored, automatic saving, import and export.
# Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
# This file is covered by the GNU General Public License, version 2.

import os

import addonHandler
import config
import gui
import wx
from gui import guiHelper, nvdaControls
from gui.settingsDialogs import SettingsPanel

addonHandler.initTranslation()

CONFIG_SECTION = "NotasWorkflowNVDA"
# Translators: type of file in the import and export dialogs.
FILE_WILDCARD = _("Notas Workflow NVDA notes (*.json)|*.json")


def askFolder(parent, current):
	"""Folder chosen by the person, or None. Module functions so the tests can replace them."""
	# Translators: title of the dialog that chooses the folder of the notes.
	dlg = wx.DirDialog(parent, _("Folder of the notes"), current or "", wx.DD_DEFAULT_STYLE)
	try:
		return dlg.GetPath() if dlg.ShowModal() == wx.ID_OK else None
	finally:
		dlg.Destroy()


def askOpenPath(parent):
	# Translators: title of the dialog that chooses the file to import.
	dlg = wx.FileDialog(parent, _("Import notes"), wildcard=FILE_WILDCARD, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
	try:
		return dlg.GetPath() if dlg.ShowModal() == wx.ID_OK else None
	finally:
		dlg.Destroy()


def askSavePath(parent):
	dlg = wx.FileDialog(
		parent,
		# Translators: title of the dialog that chooses where to export.
		_("Export notes"),
		defaultFile="notas-workflow-nvda.json",
		wildcard=FILE_WILDCARD,
		style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
	)
	try:
		return dlg.GetPath() if dlg.ShowModal() == wx.ID_OK else None
	finally:
		dlg.Destroy()


class NotasSettingsPanel(SettingsPanel):
	# Translators: name of the add-on category in NVDA settings.
	title = _("Notas Workflow NVDA")
	#: Set by the global plugin.
	plugin = None

	def makeSettings(self, settingsSizer):
		conf = config.conf[CONFIG_SECTION]
		sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		# Translators: label of the field with the folder where the notes are stored.
		self.folderEdit = sHelper.addLabeledControl(_("Notes &folder:"), wx.TextCtrl, size=(360, -1))
		self.folderEdit.SetValue(conf["dataFolder"] or (self.plugin.defaultDataFolder() if self.plugin else ""))
		folderButtons = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: button that chooses the folder of the notes.
		self.browseButton = folderButtons.addButton(self, label=_("B&rowse…"))
		# Translators: button that goes back to the default folder of the notes.
		self.defaultButton = folderButtons.addButton(self, label=_("Use the &default folder"))
		sHelper.addItem(folderButtons)
		self.autoSaveSpin = sHelper.addLabeledControl(
			# Translators: label of the number of seconds before a note is saved by itself.
			_("&Save automatically after (seconds):"),
			nvdaControls.SelectOnFocusSpinCtrl,
			min=1,
			max=30,
			initial=int(conf["autoSaveSeconds"]),
		)
		self.announceCheck = sHelper.addItem(wx.CheckBox(
			self,
			# Translators: check box of the settings.
			label=_("&Announce the automatic saving"),
		))
		self.announceCheck.SetValue(bool(conf["announceAutoSave"]))
		dataButtons = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: button that imports notes from a file exported by the add-on.
		self.importButton = dataButtons.addButton(self, label=_("&Import notes…"))
		# Translators: button that exports every note to a file.
		self.exportButton = dataButtons.addButton(self, label=_("&Export notes…"))
		sHelper.addItem(dataButtons)
		self.browseButton.Bind(wx.EVT_BUTTON, self.onBrowse)
		self.defaultButton.Bind(wx.EVT_BUTTON, self.onDefault)
		self.importButton.Bind(wx.EVT_BUTTON, self.onImport)
		self.exportButton.Bind(wx.EVT_BUTTON, self.onExport)
		hasPlugin = self.plugin is not None
		self.importButton.Enable(hasPlugin)
		self.exportButton.Enable(hasPlugin)

	def onBrowse(self, evt):
		path = askFolder(self, self.folderEdit.GetValue())
		if path:
			self.folderEdit.SetValue(path)
		self.folderEdit.SetFocus()

	def onDefault(self, evt):
		if self.plugin:
			self.folderEdit.SetValue(self.plugin.defaultDataFolder())
		self.folderEdit.SetFocus()

	def onImport(self, evt):
		path = askOpenPath(self)
		if path and self.plugin:
			self.plugin.importNotes(path)
		self.importButton.SetFocus()

	def onExport(self, evt):
		path = askSavePath(self)
		if path and self.plugin:
			self.plugin.exportNotes(path)
		self.exportButton.SetFocus()

	def chosenFolder(self):
		path = self.folderEdit.GetValue().strip()
		if self.plugin and path and os.path.normcase(os.path.abspath(path)) == os.path.normcase(os.path.abspath(self.plugin.defaultDataFolder())):
			return ""
		return path

	def isValid(self):
		path = self.chosenFolder()
		if path and not (os.path.isabs(path) and os.path.isdir(path) and os.access(path, os.W_OK)):
			gui.messageBox(
				# Translators: message when the folder typed in the settings cannot be used.
				_("The notes folder must be an existing folder that can be written. Choose it with Browse."),
				# Translators: title of a message box.
				_("Notas Workflow NVDA"),
				wx.OK | wx.ICON_WARNING,
				self,
			)
			self.folderEdit.SetFocus()
			return False
		return True

	def onSave(self):
		conf = config.conf[CONFIG_SECTION]
		folder = self.chosenFolder()
		changed = folder != conf["dataFolder"]
		conf["dataFolder"] = folder
		conf["autoSaveSeconds"] = int(self.autoSaveSpin.GetValue())
		conf["announceAutoSave"] = self.announceCheck.GetValue()
		if changed and self.plugin:
			self.plugin.changeDataFolder()
