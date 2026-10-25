# -*- coding: UTF-8 -*-
# NotasWorkflowNVDA - global plugin
# Notes in status lanes, notebooks and folders inside NVDA, with keyboard and speech.
# Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
# This file is covered by the GNU General Public License, version 2.
# See the file COPYING for more details.

import os
import re
import shutil
import threading
import time

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
#: Notes prepared for the search at a time, and the pause between batches (seconds).
INDEX_BATCH = 300
INDEX_PAUSE = 0.02
#: Name of the add-on up to 1.0.0: its settings and notes are copied once to the new name.
LEGACY_NAME = "NotasWorkflow"
LEGACY_DATA_FILE = "NotasWorkflow-data.json"
#: The user manual shown by the User manual button (addon/doc/<lang>/manual.html).
MANUAL_FILE = "manual.html"
_MAIN_RE = re.compile(r"<main\b.*?</main>", re.S)
# Translators: category of the add-on commands in the Input gestures dialog.
SCRIPT_CATEGORY = _("Notas Workflow NVDA")


def documentLanguage():
	"""Language of the exported documents (pt-BR...): the language of NVDA."""
	try:
		import languageHandler

		return (languageHandler.getLanguage() or "en").replace("_", "-")
	except Exception:
		return "en"


def manualPath():
	"""manual.html of the add-on (made by build.py from docs/manual/MANUAL.md), in the language
	of NVDA when there is one, otherwise the Brazilian Portuguese one; None when it is missing."""
	docs = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "doc"))
	lang = documentLanguage().replace("-", "_")
	for name in (lang, lang.split("_")[0], "pt_BR"):
		path = os.path.join(docs, name, MANUAL_FILE)
		if os.path.isfile(path):
			return path
	return None


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
		# Writes happen in a thread: with many notes a write takes half a second.
		self.store.enableBackgroundSaving(lambda error: wx.CallAfter(self.writeFailed, error))
		# The notes are read in a thread, so NVDA starts at once even with 100,000 notes;
		# every command waits for them with ensureLoaded().
		self._loaded = threading.Event()
		#: Set when the text of every note is prepared for the search.
		self.indexReady = threading.Event()
		self._announced = False
		self._loader = threading.Thread(target=self._loadInBackground, name="NotasWorkflowNVDA-load", daemon=True)
		self._loader.start()
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

		self._loaded.wait(60)

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
		# Nothing is lost: the last changes are written before NVDA exits.
		error = self.store.flush()
		if error is not None:
			log.error("NotasWorkflowNVDA: could not save the notes when exiting (%s)" % error.detail)
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

	def _loadInBackground(self):
		try:
			self.store.load()
		except Exception as e:
			# Never log the notes: only the kind of error.
			log.error("NotasWorkflowNVDA: could not read the notes (%s)" % type(e).__name__)
		finally:
			self._loaded.set()
		wx.CallAfter(self.ensureLoaded)
		# Prepares the text of the search now, so the first search is as fast as the others.
		# Small batches with pauses: Python runs one thread at a time, and NVDA must keep
		# answering while this runs.
		notes = list(self.store.notes)
		try:
			for start in range(0, len(notes), INDEX_BATCH):
				for note in notes[start:start + INDEX_BATCH]:
					self.searchIndex.entry(note)
				time.sleep(INDEX_PAUSE)
		except Exception:
			log.debugWarning("NotasWorkflowNVDA: could not prepare the notes for the search", exc_info=True)
		finally:
			self.indexReady.set()

	def ensureLoaded(self):
		"""Waits for the notes (read in a thread when NVDA starts) and says, once, what happened."""
		if not self._loaded.is_set():
			# Translators: spoken when a command is used while the notes are still being read.
			self.speak(_("Loading the notes…"))
			self._loaded.wait()
		if self._announced:
			return
		self._announced = True
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

	def writeFailed(self, error):
		"""A write in the background failed: the notes stay open and the next change tries again."""
		log.warning("NotasWorkflowNVDA: write (%s)" % error.detail)
		self.speak(messages.storeError(error, self.store.folder))

	def reloadIfChanged(self):
		"""Reads the notes again when another computer changed the file. True when it did."""
		self.ensureLoaded()
		try:
			if self.store.reloadIfChanged():
				self.announceWarning()
				return True
		except Exception as e:
			log.error("NotasWorkflowNVDA: could not read the notes again (%s)" % type(e).__name__)
		return False

	def changeDataFolder(self):
		"""After the settings change the folder: its notes or a copy of the current ones."""
		self.ensureLoaded()
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
		self.ensureLoaded()
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
		self.ensureLoaded()
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
				if noteId:
					dlg.noteChanged(noteId)
				else:
					dlg.refresh(dlg.selectedNoteId())
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

		self.ensureLoaded()
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
		index = prompts.choosePlace(
			parent,
			# Translators: title of the dialog that moves a note to a notebook or folder.
			_("Move {title} to").format(title=messages.noteTitle(note)),
			self.store,
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

	# -- export as a document --------------------------------------------------------------

	def exportPlan(self, kind, ident):
		"""What exporting a note, notebook or folder writes: (name, document title, sections,
		number of notes) or None when it no longer exists. sections: [(heading or None, notes,
		subfolder name or None)], with copies of the notes (they may change while the file is
		written); the subfolder is where the notes go when each note is a file."""
		def lanes(notes):
			grouped = model.byLane(notes)
			return [dict(n) for lane in model.LANE_IDS for n in grouped[lane]]

		if kind == "note":
			note = self.store.getNote(ident)
			if note is None:
				return None
			return messages.noteTitle(note), None, [(None, [dict(note)], None)], 1
		if kind == "notebook":
			notebook = self.store.getNotebook(ident)
			if notebook is None:
				return None
			notes = lanes(self.store.notesIn(ident))
			return notebook["name"], messages.notebookPlace(notebook), [(None, notes, None)], len(notes)
		folder = self.store.getFolder(ident)
		if folder is None:
			return None
		sections = [(messages.directInFolder(), lanes(self.store.notesInFolder(ident)), None)]
		for notebook in self.store.notebooksIn(ident):
			sections.append((messages.notebookPlace(notebook), lanes(self.store.notesIn(notebook["id"])), notebook["name"]))
		return folder["name"], messages.folderPlace(folder), sections, sum(len(s[1]) for s in sections)

	def exportItem(self, parent, kind, ident):
		"""Export… of the main window: asks the format, one file or one per note (notebook and
		folder) and where, then writes in the background and speaks the result.
		kind: note, notebook or folder. True when the export started."""
		from . import exporter

		self.ensureLoaded()
		plan = self.exportPlan(kind, ident)
		if plan is None:
			self.speak(messages.storeError(StoreError("notFound")))
			return False
		name, title, sections, count = plan
		if not count:
			self.speak(messages.nothingToExport(title))
			return False
		# Translators: title of the dialogs that export notes.
		caption = _("Export")
		index = prompts.chooseItem(
			parent,
			# Translators: question of the dialog that chooses the format of the export; {name} is what is exported.
			_("Export {name} as:").format(name=title or name),
			caption,
			messages.exportFormats(),
		)
		if index is None:
			return False
		fmt = exporter.FORMATS[index]
		separate = False
		if kind != "note":
			mode = prompts.chooseItem(
				parent,
				# Translators: question of the dialog that chooses one file or one file per note; {count} is "3 notes".
				_("How to export {count}:").format(count=messages.notesCount(count)),
				caption,
				messages.exportModes(),
			)
			if mode is None:
				return False
			separate = mode == 1
		if separate:
			# Translators: title of the dialog that chooses where the folder of the exported notes is created.
			target = prompts.askFolder(parent, _("Choose where to create the folder {name}").format(name=name))
		else:
			target = prompts.askSaveFile(
				parent,
				# Translators: title of the dialog that chooses the exported file; {name} is what is exported.
				_("Export {name}").format(name=name),
				exporter.safeName(name, messages.untitled()) + exporter.EXTENSIONS[fmt],
				messages.exportWildcard(fmt),
			)
		if not target:
			return False
		if not separate and not target.lower().endswith(exporter.EXTENSIONS[fmt]):
			target += exporter.EXTENSIONS[fmt]
		place = messages.placeOf(self.store, sections[0][1][0]) if kind == "note" else ""
		self.exportThread = threading.Thread(
			target=self._writeExport,
			args=(exporter, fmt, separate, target, name, title, sections, count, place),
			name="NotasWorkflowNVDA export",
			daemon=True,
		)
		self.exportThread.start()
		return True

	def _writeExport(self, exporter, fmt, separate, target, name, title, sections, count, place):
		"""Runs in a thread: builds and writes the document(s), then speaks the result."""
		lang = documentLanguage()
		fallback = messages.untitled()

		def describe(note):
			return messages.noteDetails(note, place)

		try:
			if separate:
				groups = [(subfolder, notes) for _heading, notes, subfolder in sections]
				folder, written = exporter.writeSeparate(
					target, name, fmt, groups,
					lambda note: exporter.buildDocument(None, None, [(None, [note])], describe, messages.noteTitle),
					messages.noteTitle, lang, fallback,
				)
				result = messages.exportedSeparate(written, folder)
			else:
				intro = messages.exportIntro(count) if title is not None else None
				blocks = exporter.buildDocument(title, intro, [(heading, notes) for heading, notes, _s in sections], describe, messages.noteTitle)
				exporter.writeDocument(target, fmt, blocks, title or name, lang)
				result = messages.exported(count, os.path.basename(target))
		except Exception as e:
			# Never log the notes or the path: only the kind of error.
			log.warning("NotasWorkflowNVDA: export (%s)" % type(e).__name__)
			result = messages.exportFailed(target)
		self.speak(result)

	def editNote(self, parent, noteId, focusContent=False):
		from .noteDialog import NoteDialog

		self.ensureLoaded()

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

		self.ensureLoaded()

		dlg = SearchDialog(parent or gui.mainFrame, self, query)
		try:
			dlg.ShowModal()
			return dlg.openedId
		finally:
			# The window may have destroyed itself already.
			if dlg:
				dlg.timer.Stop()
				dlg.Destroy()

	def openManual(self):
		"""Shows the user manual in NVDA's browseable window (headings, lists and tables
		navigable in browse mode). Returns False when the manual is missing."""
		path = manualPath()
		try:
			with open(path, encoding="utf-8") as f:
				m = _MAIN_RE.search(f.read())
		except (OSError, TypeError, UnicodeDecodeError):
			m = None
		if m is None:
			log.error("NotasWorkflowNVDA: user manual not found")
			# Translators: spoken when the file of the user manual is missing.
			self.speak(_("The user manual was not found. Install the add-on again."))
			return False
		# Translators: title of the window with the user manual.
		ui.browseableMessage(m.group(0), _("Notas Workflow NVDA user manual"), isHtml=True)
		return True

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

	@script(
		# Translators: description of a command in the Input gestures dialog.
		description=_("Notas Workflow NVDA: opens the user manual"),
	)
	def script_openManual(self, gesture):
		wx.CallAfter(self.openManual)
