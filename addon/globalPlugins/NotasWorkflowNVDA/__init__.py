# -*- coding: UTF-8 -*-
# NotasWorkflowNVDA - global plugin
# Notes in status lanes, notebooks and folders inside NVDA, with keyboard and speech.
# Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
# This file is covered by the GNU General Public License, version 2.
# See the file COPYING for more details.

import os
import shutil

import addonHandler
import config
import globalPluginHandler
import globalVars
import gui
import queueHandler
import ui
import wx
from logHandler import log
from scriptHandler import script

from . import messages, model, prompts
from .search import SearchIndex
from .store import NotesStore, StoreError

addonHandler.initTranslation()

CONFIG_SECTION = "NotasWorkflowNVDA"
CONFIG_SPEC = {
	"dataFolder": "string(default='')",
	"autoSaveSeconds": "integer(default=2, min=1, max=30)",
	"announceAutoSave": "boolean(default=False)",
	"legacyChecked": "boolean(default=False)",
}
DATA_SUBFOLDER = "NotasWorkflowNVDA"
#: Name of the add-on up to 1.0.0: its settings and notes are copied once to the new name.
LEGACY_NAME = "NotasWorkflow"
LEGACY_DATA_FILE = "NotasWorkflow-data.json"
# Translators: category of the add-on commands in the Input gestures dialog.
SCRIPT_CATEGORY = _("Notas Workflow NVDA")


def disableInSecureMode(cls):
	"""Does not load the add-on on secure screens (logon, UAC), as recommended by NV Access."""
	if globalVars.appArgs.secure:
		return globalPluginHandler.GlobalPlugin
	return cls


@disableInSecureMode
class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = SCRIPT_CATEGORY

	def __init__(self):
		super().__init__()
		config.conf.spec[CONFIG_SECTION] = CONFIG_SPEC
		self.migrateLegacy()
		self.store = NotesStore(self.dataFolder())
		#: The note window open at the moment (its changes are saved if NVDA exits).
		self.openEditor = None
		#: Prepared text of the notes for the search, kept while the notes do not change.
		self.searchIndex = SearchIndex()
		self.loadStore()
		from .settingsPanel import NotasSettingsPanel

		NotasSettingsPanel.plugin = self
		self._settingsPanelClass = NotasSettingsPanel
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(NotasSettingsPanel)
		self._menuItem = None
		try:
			toolsMenu = gui.mainFrame.sysTrayIcon.toolsMenu
			self._menuItem = toolsMenu.Append(
				wx.ID_ANY,
				# Translators: item of the NVDA Tools menu.
				_("&Notas Workflow NVDA…"),
				# Translators: help text of the Tools menu item.
				_("Opens the Notas Workflow NVDA window: notes in lanes, notebooks and folders"),
			)
			gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, lambda evt: self.openWindow(), self._menuItem)
		except Exception:
			log.debugWarning("NotasWorkflowNVDA: could not add the Tools menu item", exc_info=True)

	def terminate(self):
		from .mainDialog import NotesDialog

		if self.openEditor:
			try:
				self.openEditor.save()
			except Exception:
				log.debugWarning("NotasWorkflowNVDA: could not save the open note", exc_info=True)

		try:
			NotesDialog.closeInstance()
		except Exception:
			log.debugWarning("NotasWorkflowNVDA: could not close the window", exc_info=True)
		if self._settingsPanelClass.plugin is self:
			self._settingsPanelClass.plugin = None
		try:
			gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(self._settingsPanelClass)
		except ValueError:
			pass
		if self._menuItem is not None:
			try:
				gui.mainFrame.sysTrayIcon.toolsMenu.Remove(self._menuItem)
			except Exception:
				log.debugWarning("NotasWorkflowNVDA: could not remove the Tools menu item", exc_info=True)
		super().terminate()

	# -- configuration and data ------------------------------------------------------------

	def getConfig(self, key):
		return config.conf[CONFIG_SECTION][key]

	def setConfig(self, key, value):
		config.conf[CONFIG_SECTION][key] = value

	def defaultDataFolder(self):
		return os.path.join(globalVars.appArgs.configPath, DATA_SUBFOLDER)

	def dataFolder(self):
		return self.getConfig("dataFolder") or self.defaultDataFolder()

	def migrateLegacy(self):
		"""First start after the rename from NotasWorkflow (1.0.0): copies its settings and the
		notes of its default folder. Nothing of the old add-on is moved or deleted."""
		self._legacyCopied = False
		conf = config.conf[CONFIG_SECTION]
		if conf["legacyChecked"]:
			return
		conf["legacyChecked"] = True
		try:
			legacy = dict(config.conf.profiles[0].get(LEGACY_NAME) or {})
		except Exception:
			legacy = {}
		try:
			if isinstance(legacy.get("dataFolder"), str) and legacy["dataFolder"] and not conf["dataFolder"]:
				conf["dataFolder"] = legacy["dataFolder"]
			if str(legacy.get("autoSaveSeconds", "")).isdigit():
				conf["autoSaveSeconds"] = max(1, min(30, int(legacy["autoSaveSeconds"])))
			if str(legacy.get("announceAutoSave")) in ("True", "False"):
				conf["announceAutoSave"] = str(legacy["announceAutoSave"]) == "True"
		except Exception:
			log.debugWarning("NotasWorkflowNVDA: could not read the settings of NotasWorkflow", exc_info=True)
		if conf["dataFolder"]:
			# A chosen folder: the store copies the old file of that folder by itself.
			return
		oldFolder = os.path.join(globalVars.appArgs.configPath, LEGACY_NAME)
		newFolder = self.defaultDataFolder()
		newFile = NotesStore(newFolder).path
		if os.path.exists(newFile):
			return
		for suffix in ("", ".bak"):
			old = os.path.join(oldFolder, LEGACY_DATA_FILE + suffix)
			if os.path.isfile(old):
				try:
					os.makedirs(newFolder, exist_ok=True)
					shutil.copy2(old, newFile + suffix)
					self._legacyCopied = True
				except OSError as e:
					log.warning("NotasWorkflowNVDA: could not copy the notes of NotasWorkflow (%s)" % type(e).__name__)

	def loadStore(self):
		try:
			self.store.load()
		except Exception as e:
			# Never log the notes: only the kind of error.
			log.error("NotasWorkflowNVDA: could not read the notes (%s)" % type(e).__name__)
		self.announceWarning()
		if self._legacyCopied or self.store.migrated:
			self._legacyCopied = False
			log.info("NotasWorkflowNVDA: notes of NotasWorkflow 1.0.0 copied")
			# Translators: spoken at the first start after the add-on was renamed; {count} is "2 notes".
			self.speak(_("Notes of the previous version brought to Notas Workflow NVDA: {count}. The old add-on can be uninstalled.").format(count=messages.notesCount(len(self.store.notes))))

	def announceWarning(self):
		warning = self.store.warning
		if warning and warning[0] == "corrupt":
			log.warning("NotasWorkflowNVDA: damaged data file kept as %s" % warning[1])
			self.speak(messages.corruptWarning(warning[1], warning[2]))
			self.store.warning = None

	def reloadIfChanged(self):
		try:
			if self.store.reloadIfChanged():
				self.announceWarning()
		except Exception as e:
			log.error("NotasWorkflowNVDA: could not read the notes again (%s)" % type(e).__name__)

	def changeDataFolder(self):
		"""After the settings change the folder: its notes or a copy of the current ones."""
		folder = self.dataFolder()
		ok, result = self.safe(self.store.relocate, folder)
		if not ok:
			return
		self.announceWarning()
		if result == "loaded":
			# Translators: spoken after choosing a folder that already had notes.
			self.speak(_("Using the notes of the new folder: {count}").format(count=messages.notesCount(len(self.store.notes))))
		else:
			# Translators: spoken after the notes were written to the new folder.
			self.speak(_("Notes saved in the new folder"))
		self.notesChanged()

	def importNotes(self, path):
		ok, counts = self.safe(self.store.importFile, path)
		if not ok:
			return None
		# Translators: spoken after importing; {notes} is "3 notes", {notebooks} "2 notebooks", {folders} a number.
		self.speak(_("Imported: {notes}, {notebooks}, {folders} folders").format(
			notes=messages.notesCount(counts["notes"]),
			notebooks=messages.notebooksCount(counts["notebooks"]),
			folders=counts["folders"],
		))
		self.notesChanged()
		return counts

	def exportNotes(self, path):
		ok, _r = self.safe(self.store.exportFile, path)
		if ok:
			# Translators: spoken after exporting.
			self.speak(_("Exported: {count}").format(count=messages.notesCount(len(self.store.notes))))
		return ok

	def safe(self, func, *args, **kwargs):
		"""(True, result) or (False, None) after speaking the problem."""
		try:
			return True, func(*args, **kwargs)
		except StoreError as e:
			log.warning("NotasWorkflowNVDA: %s (%s)" % (e.kind, e.detail))
			self.speak(messages.storeError(e, self.store.folder))
			return False, None

	def speak(self, text):
		queueHandler.queueFunction(queueHandler.eventQueue, ui.message, text)

	def notesChanged(self, noteId=None):
		"""Called after the notes change outside the main window (editor, settings)."""
		from .mainDialog import NotesDialog

		dlg = NotesDialog._instance
		if dlg:
			try:
				dlg.refresh(noteId or dlg.selectedNoteId())
			except Exception:
				log.debugWarning("NotasWorkflowNVDA: could not refresh the window", exc_info=True)

	# -- windows ---------------------------------------------------------------------------

	def _popup(self, func):
		gui.mainFrame.prePopup()
		try:
			return func()
		finally:
			gui.mainFrame.postPopup()

	def openWindow(self):
		from .mainDialog import NotesDialog

		return self._popup(lambda: NotesDialog.open(self))

	def newNote(self, parent=None, laneId=model.DEFAULT_LANE, notebookId=None, folderId=None):
		"""New note window, then the note window. Returns the id of the new note or None."""
		from .noteDialog import NewNoteDialog

		dlg = NewNoteDialog(parent or gui.mainFrame, self.store, laneId, notebookId, folderId)
		try:
			if dlg.ShowModal() != wx.ID_OK:
				return None
			values = dlg.values()
		finally:
			dlg.Destroy()
		if not values["title"]:
			return None
		ok, note = self.safe(self.store.addNote, values["title"], values["laneId"], values["notebookId"], values["folderId"])
		if not ok:
			return None
		# Translators: spoken after a note is created; {lane} is its status.
		self.speak(_("Note created in {lane}").format(lane=messages.laneName(note["laneId"])))
		self.editNote(parent, note["id"], focusContent=True)
		return note["id"]

	def createNotebook(self, parent, folderId=None):
		"""Asks the name and creates a notebook (inside folderId). Returns it or None."""
		folder = self.store.getFolder(folderId) if folderId else None
		# Translators: title of the dialog that creates a notebook.
		name = prompts.askText(parent, messages.askNotebookName(folder), _("New notebook"))
		if name is None or not name.strip():
			return None
		ok, notebook = self.safe(self.store.addNotebook, name, folderId)
		if not ok:
			return None
		self.speak(messages.notebookCreated(notebook["name"]))
		return notebook

	def createFolder(self, parent):
		"""Asks the name and creates a folder. Returns it or None."""
		# Translators: question and title of the dialog that creates a folder.
		name = prompts.askText(parent, _("Name of the new folder:"), _("New folder"))
		if name is None or not name.strip():
			return None
		ok, folder = self.safe(self.store.addFolder, name)
		if not ok:
			return None
		self.speak(messages.folderCreated(folder["name"]))
		return folder

	def moveNote(self, parent, note):
		"""Move to: chooses a notebook, a folder or loose and moves the note. True when moved."""
		labels, places = messages.locationChoices(self.store)
		current = (note["notebookId"], None) if note["notebookId"] else (None, note["folderId"])
		index = prompts.chooseItem(
			parent,
			# Translators: question of the dialog that moves a note to a notebook or folder.
			_("Move {title} to:").format(title=messages.noteTitle(note)),
			# Translators: title of the dialog that moves a note to a notebook or folder.
			_("Move to"),
			labels,
			places.index(current) if current in places else 0,
		)
		if index is None or places[index] == current:
			return False
		notebookId, folderId = places[index]
		ok, _changed = self.safe(self.store.moveNoteTo, note["id"], notebookId, folderId)
		if ok:
			self.speak(messages.movedToPlace(labels[index]))
		return ok

	def deleteNote(self, parent, note):
		"""Asks and deletes a note. True when deleted."""
		answer = gui.messageBox(
			# Translators: confirmation before deleting a note.
			_("Delete the note {title}? This cannot be undone.").format(title=messages.noteTitle(note)),
			# Translators: title of the confirmation before deleting a note.
			_("Delete note"),
			wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
			parent,
		)
		if answer != wx.YES:
			return False
		ok, _r = self.safe(self.store.deleteNote, note["id"])
		if ok:
			# Translators: spoken after a note is deleted.
			self.speak(_("Note deleted: {title}").format(title=messages.noteTitle(note)))
		return ok

	def editNote(self, parent, noteId, focusContent=False):
		from .noteDialog import NoteDialog

		if self.store.getNote(noteId) is None:
			self.speak(messages.storeError(StoreError("notFound")))
			return
		dlg = NoteDialog(parent or gui.mainFrame, self, noteId)
		self.openEditor = dlg
		try:
			if focusContent:
				dlg.contentEdit.SetFocus()
			else:
				dlg.titleEdit.SetFocus()
			dlg.ShowModal()
		finally:
			self.openEditor = None
			# The window may have destroyed itself already.
			if dlg:
				dlg.timer.Stop()
				dlg.Destroy()

	def openSearch(self, parent=None, query=""):
		"""Search window. Returns the id of the last note opened from it, or None."""
		from .searchDialog import SearchDialog

		dlg = SearchDialog(parent or gui.mainFrame, self, query)
		try:
			dlg.ShowModal()
			return dlg.openedId
		finally:
			# The window may have destroyed itself already.
			if dlg:
				dlg.timer.Stop()
				dlg.Destroy()

	def lanesSummary(self):
		counts = {lane: len(notes) for lane, notes in model.byLane(self.store.notes).items()}
		return messages.lanesSummary(counts)

	# -- scripts ---------------------------------------------------------------------------

	@script(
		# Translators: description of a command in the Input gestures dialog.
		description=_("Opens the Notas Workflow NVDA window with the notes in lanes"),
		gesture="kb:NVDA+alt+n",
	)
	def script_openWindow(self, gesture):
		wx.CallAfter(self.openWindow)

	@script(
		# Translators: description of a command in the Input gestures dialog.
		description=_("Notas Workflow NVDA: creates a note"),
		gesture="kb:NVDA+alt+f",
	)
	def script_newNote(self, gesture):
		wx.CallAfter(self._popup, lambda: self.notesChanged(self.newNote()))

	@script(
		# Translators: description of a command in the Input gestures dialog.
		description=_("Notas Workflow NVDA: searches the notes"),
		gesture="kb:NVDA+alt+b",
	)
	def script_search(self, gesture):
		wx.CallAfter(self._popup, self.openSearch)

	@script(
		# Translators: description of a command in the Input gestures dialog.
		description=_("Notas Workflow NVDA: says how many notes each lane has"),
	)
	def script_lanesSummary(self, gesture):
		self.reloadIfChanged()
		self.speak(self.lanesSummary())
