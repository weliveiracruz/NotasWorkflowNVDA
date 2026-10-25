# -*- coding: UTF-8 -*-
# NotasWorkflowNVDA - store.py
# The operations on notes, notebooks and folders and their persistence
# in a JSON file written atomically with a backup copy.
# No wx and no NVDA modules here.
# Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
# This file is covered by the GNU General Public License, version 2.

import datetime
import json
import os
import shutil
import threading
import time

from . import model

FILE_NAME = "NotasWorkflowNVDA-data.json"
#: Name of the data file up to 1.0.0, when the add-on was called NotasWorkflow.
LEGACY_FILE_NAME = "NotasWorkflow-data.json"
FORMAT = "notas-workflow"
VERSION = 1
#: Data and import files above this size are refused without being read.
MAX_FILE_SIZE = 200 * 1024 * 1024
#: The background write waits this long after the last change (several changes, one write).
WRITE_DELAY = 0.5
#: Notes encoded between two pauses of the background write (NVDA keeps answering).
WRITE_BATCH = 500
WRITE_PAUSE = 0.003
#: Keys of older exports (browser storage), still accepted on import.
WEB_PREFIX = "notas-workflow:"


class StoreError(Exception):
	"""kind: write, corrupt, tooLarge, invalidImport, notFound."""

	def __init__(self, kind, detail=""):
		super().__init__(kind)
		self.kind = kind
		self.detail = str(detail)[:200]


def _readJson(path):
	"""Parsed JSON of a file, refusing big files before reading them."""
	size = os.path.getsize(path)
	if size > MAX_FILE_SIZE:
		raise StoreError("tooLarge")
	with open(path, "rb") as f:
		raw = f.read(MAX_FILE_SIZE + 1)
	if len(raw) > MAX_FILE_SIZE:
		raise StoreError("tooLarge")
	text = raw.decode("utf-8-sig")
	try:
		return json.loads(text)
	except RecursionError:
		# A hostile file with thousands of nested lists or objects.
		raise ValueError("too deeply nested")


def _jsonChunks(data):
	"""The data as compact JSON, note by note. json.dumps would hold Python for the whole
	file (about a second with 100,000 notes) and NVDA would stop answering meanwhile."""
	encode = json.JSONEncoder(ensure_ascii=False, separators=(",", ":")).encode
	yield '{"format":%s,"version":%d,"folders":%s,"notebooks":%s,"notes":[' % (
		encode(data["format"]), data["version"], encode(data["folders"]), encode(data["notebooks"]))
	batch = []
	for i, note in enumerate(data["notes"]):
		batch.append(("," if i else "") + encode(note))
		if len(batch) >= WRITE_BATCH:
			yield "".join(batch)
			batch = []
			# Gives the turn to NVDA: a short real pause, not just a switch.
			time.sleep(WRITE_PAUSE)
	batch.append("]}")
	yield "".join(batch)


def parseData(data, now=None):
	"""(folders, notebooks, notes) validated from data of this add-on.

	Accepts {"folders", "notebooks", "notes"}, the keys of older exports
	("notas-workflow:notes"...) or just a list of notes. Raises ValueError otherwise."""
	now = now or model.nowIso()
	if isinstance(data, list):
		data = {"notes": data}
	if not isinstance(data, dict):
		raise ValueError("not an object")
	for key in ("notes", "notebooks", "folders"):
		if key not in data and WEB_PREFIX + key in data:
			value = data[WEB_PREFIX + key]
			if isinstance(value, str):
				# localStorage keeps the arrays as JSON text.
				value = json.loads(value)
			data[key] = value
	if isinstance(data.get("notes"), dict):
		# Some exports keep the notes as {id: note}.
		data["notes"] = list(data["notes"].values())
	if not any(isinstance(data.get(k), list) for k in ("notes", "notebooks", "folders")):
		raise ValueError("no notes")
	folders = _unique(model.sanitizeFolder(f, now) for f in _list(data.get("folders")))
	folderIds = {f["id"] for f in folders}
	notebooks = _unique(model.sanitizeNotebook(nb, now, folderIds) for nb in _list(data.get("notebooks")))
	notebookIds = {nb["id"] for nb in notebooks}
	notes = _unique(model.sanitizeNote(n, now, notebookIds, folderIds) for n in _list(data.get("notes")))
	return folders, notebooks, notes


def _list(value):
	return value if isinstance(value, list) else []


def _unique(items):
	out = []
	seen = set()
	for item in items:
		if item is not None and item["id"] not in seen:
			seen.add(item["id"])
			out.append(item)
	return out


class _Writer:
	"""Writes the file in a thread. Changes made while a write is running become a single
	next write (only the latest state is written)."""

	def __init__(self, store, onError):
		self.store = store
		self.onError = onError
		self.lastError = None
		self._lock = threading.Lock()
		self._pending = None
		self._wake = threading.Event()
		self._idle = threading.Event()
		self._idle.set()
		self._thread = threading.Thread(target=self._loop, name="NotasWorkflowNVDA-save", daemon=True)
		self._thread.start()

	def request(self, data):
		with self._lock:
			self._pending = data
			self._idle.clear()
			self._wake.set()

	def busy(self):
		return not self._idle.is_set()

	def flush(self, timeout=120):
		"""Waits until everything requested is written. Returns the error of a failed write, or None."""
		self._idle.wait(timeout)
		error, self.lastError = self.lastError, None
		return error

	def _loop(self):
		while True:
			self._wake.wait()
			# Waits for the changes to stop for a moment: a series of changes is written once.
			while True:
				with self._lock:
					self._wake.clear()
				if not self._wake.wait(WRITE_DELAY):
					break
			with self._lock:
				data, self._pending = self._pending, None
				self._wake.clear()
			if data is not None:
				try:
					self.store._write(data)
					self.lastError = None
				except StoreError as e:
					self.lastError = e
					if self.onError is not None:
						self.onError(e)
			with self._lock:
				if self._pending is None:
					self._idle.set()


class NotesStore:
	def __init__(self, folder):
		self.folder = folder
		self.folders = []
		self.notebooks = []
		self.notes = []
		self._stamp = None
		#: (kind, detail) of the last problem found while loading, for the interface.
		self.warning = None
		#: True when the last load copied a data file of NotasWorkflow 1.0.0.
		self.migrated = False
		self._writer = None

	@property
	def path(self):
		return os.path.join(self.folder, FILE_NAME)

	@property
	def backupPath(self):
		return self.path + ".bak"

	# -- file -------------------------------------------------------------------------------

	def _fileStamp(self):
		try:
			st = os.stat(self.path)
			return (st.st_size, st.st_mtime_ns)
		except OSError:
			return None

	def adoptLegacyFile(self):
		"""Copies the data file of NotasWorkflow 1.0.0 of this folder to the new name when
		there is no file with the new name yet. The old file is never moved or deleted."""
		legacy = os.path.join(self.folder, LEGACY_FILE_NAME)
		if os.path.exists(self.path) or not os.path.isfile(legacy):
			return False
		try:
			shutil.copy2(legacy, self.path)
		except OSError:
			return False
		return True

	def load(self):
		"""Reads the file. A damaged file is kept with another name and the backup is used."""
		self.flush()
		self.migrated = self.adoptLegacyFile()
		self.warning = None
		self.folders, self.notebooks, self.notes = [], [], []
		if not os.path.exists(self.path):
			self._stamp = None
			return
		try:
			self._apply(parseData(_readJson(self.path)))
		except (StoreError, ValueError, UnicodeDecodeError, OSError):
			saved = self._keepDamaged()
			restored = False
			try:
				if os.path.exists(self.backupPath):
					self._apply(parseData(_readJson(self.backupPath)))
					restored = True
			except (StoreError, ValueError, UnicodeDecodeError, OSError):
				self.folders, self.notebooks, self.notes = [], [], []
			self.warning = ("corrupt", os.path.basename(saved) if saved else "", restored)
			if restored:
				try:
					self.save()
				except StoreError:
					pass
			return
		self._stamp = self._fileStamp()

	def _apply(self, parsed):
		self.folders, self.notebooks, self.notes = (list(x) for x in parsed)

	def _keepDamaged(self):
		stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
		target = os.path.join(self.folder, "NotasWorkflowNVDA-data.corrupt-%s.json" % stamp)
		try:
			os.replace(self.path, target)
			return target
		except OSError:
			return None

	def toData(self):
		"""What is written: copies of the lists, so a write in a thread is not disturbed
		by notes added or removed meanwhile."""
		return {
			"format": FORMAT,
			"version": VERSION,
			"folders": list(self.folders),
			"notebooks": list(self.notebooks),
			"notes": list(self.notes),
		}

	def enableBackgroundSaving(self, onError=None):
		"""From now on save() returns at once and a thread writes the file (with 100,000 notes
		a write takes about half a second). onError(StoreError) is called by that thread.
		flush() waits for the write: call it before NVDA exits."""
		if self._writer is None:
			self._writer = _Writer(self, onError)

	def flush(self):
		"""Waits for the background write, if any. Returns the error of a failed write, or None."""
		return self._writer.flush() if self._writer is not None else None

	def save(self):
		if self._writer is not None:
			self._writer.request(self.toData())
			return
		self._write(self.toData())

	def _write(self, data):
		"""Atomic write: temporary file, backup of the previous file, os.replace."""
		tmp = self.path + ".tmp"
		try:
			os.makedirs(self.folder, exist_ok=True)
			with open(tmp, "w", encoding="utf-8", newline="\n") as f:
				for chunk in _jsonChunks(data):
					f.write(chunk)
				f.flush()
				os.fsync(f.fileno())
			if os.path.exists(self.path):
				try:
					os.replace(self.path, self.backupPath)
				except OSError:
					pass
			os.replace(tmp, self.path)
		except OSError as e:
			try:
				os.remove(tmp)
			except OSError:
				pass
			raise StoreError("write", type(e).__name__)
		self._stamp = self._fileStamp()

	def changedOnDisk(self):
		if self._writer is not None and self._writer.busy():
			# Our own write is running: the file is not someone else's.
			return False
		return self._fileStamp() != self._stamp

	def reloadIfChanged(self):
		"""Reads the file again when another program (a synced folder) changed it."""
		if self.changedOnDisk():
			self.load()
			return True
		return False

	def relocate(self, folder):
		"""Uses another folder: its notes when it has them ("loaded"), otherwise the
		current notes are written there ("copied")."""
		self.flush()
		old = self.folder
		self.folder = folder
		if os.path.exists(self.path):
			self.load()
			return "loaded"
		try:
			self._write(self.toData())
		except StoreError:
			self.folder = old
			raise
		return "copied"

	# -- import and export ------------------------------------------------------------------

	def importFile(self, path):
		"""Joins the notes of an exported file. Same id: the one changed
		last wins. Returns {"notes": n, "notebooks": n, "folders": n} with what was added or updated."""
		try:
			data = _readJson(path)
		except (ValueError, UnicodeDecodeError, OSError) as e:
			raise StoreError("invalidImport", type(e).__name__)
		try:
			folders, notebooks, notes = parseData(data)
		except (ValueError, TypeError) as e:
			raise StoreError("invalidImport", type(e).__name__)
		counts = {"notes": 0, "notebooks": 0, "folders": 0}
		known = {f["id"] for f in self.folders}
		for f in folders:
			if f["id"] not in known:
				self.folders.append(f)
				counts["folders"] += 1
		known = {nb["id"] for nb in self.notebooks}
		for nb in notebooks:
			if nb["id"] not in known:
				self.notebooks.append(nb)
				counts["notebooks"] += 1
		index = {n["id"]: i for i, n in enumerate(self.notes)}
		for note in notes:
			i = index.get(note["id"])
			if i is None:
				self.notes.append(note)
				counts["notes"] += 1
			elif model.updatedKey(note) > model.updatedKey(self.notes[i]):
				self.notes[i] = note
				counts["notes"] += 1
		# Notes were appended and replaced: rebuild the index by id.
		self.notes = self.notes
		if any(counts.values()):
			self.save()
		return counts

	def exportFile(self, path):
		try:
			with open(path, "w", encoding="utf-8", newline="\n") as f:
				json.dump(self.toData(), f, ensure_ascii=False, separators=(",", ":"))
		except OSError as e:
			raise StoreError("write", type(e).__name__)

	# -- reading ----------------------------------------------------------------------------

	@property
	def notes(self):
		"""The notes in order. Change them only through the methods of the store (or assign a
		new list): the index by id follows appends, removals and new lists, not items replaced in place."""
		return self._notes

	@notes.setter
	def notes(self, value):
		self._notes = value
		self._byId = {n["id"]: n for n in value}

	def getNote(self, noteId):
		"""O(1) with an index by id (rebuilt if the list was changed directly)."""
		note = self._byId.get(noteId)
		if note is None or note["id"] != noteId or len(self._byId) != len(self._notes):
			self._byId = {n["id"]: n for n in self._notes}
			note = self._byId.get(noteId)
		return note

	def getNotebook(self, notebookId):
		return next((nb for nb in self.notebooks if nb["id"] == notebookId), None)

	def getFolder(self, folderId):
		return next((f for f in self.folders if f["id"] == folderId), None)

	def notebookName(self, notebookId):
		nb = self.getNotebook(notebookId) if notebookId else None
		return nb["name"] if nb else ""

	def filtered(self, activeFilter):
		return model.filterNotes(self.notes, self.notebooks, activeFilter)

	def notebooksIn(self, folderId):
		return [nb for nb in self.notebooks if nb["folderId"] == folderId]

	def notesIn(self, notebookId):
		return [n for n in self.notes if n["notebookId"] == notebookId]

	# -- notes -----------------------------------------------------------------------------

	def _need(self, item, kind="note"):
		if item is None:
			raise StoreError("notFound", kind)
		return item

	def addNote(self, title, laneId=model.DEFAULT_LANE, notebookId=None, folderId=None, content=""):
		notebookId, folderId = self.location(notebookId, folderId)
		note = model.makeNote(title, laneId, notebookId, folderId, content[:model.MAX_CONTENT] if isinstance(content, str) else "")
		self.notes.append(note)
		self._byId[note["id"]] = note
		self.save()
		return note

	def updateNote(self, noteId, **patch):
		"""Changes the given fields; updatedAt only changes when something really changed.
		Returns True when the note changed."""
		note = self._need(self.getNote(noteId))
		clean = {}
		if "title" in patch:
			clean["title"] = model.cleanText(patch["title"], model.MAX_TITLE)
		if "content" in patch:
			content = patch["content"] if isinstance(patch["content"], str) else ""
			clean["content"] = content[:model.MAX_CONTENT]
		if "tags" in patch:
			clean["tags"] = model.cleanTags(patch["tags"])
		if "laneId" in patch and patch["laneId"] in model.LANE_IDS:
			clean["laneId"] = patch["laneId"]
		if "notebookId" in patch:
			nb = patch["notebookId"]
			clean["notebookId"] = nb if nb is None or self.getNotebook(nb) else None
		if "folderId" in patch:
			folder = patch["folderId"]
			clean["folderId"] = folder if folder is None or self.getFolder(folder) else None
		changed = {k: v for k, v in clean.items() if note.get(k) != v}
		if not changed:
			return False
		note.update(changed)
		note["updatedAt"] = model.nowIso()
		self.save()
		return True

	def deleteNote(self, noteId):
		note = self._need(self.getNote(noteId))
		self.notes.remove(note)
		self._byId.pop(noteId, None)
		self.save()

	def moveNote(self, noteId, laneId):
		return self.updateNote(noteId, laneId=laneId)

	def placeNoteBeside(self, noteId, otherId, after):
		"""Puts the note just before (after=False) or just after (after=True) another one: the
		order of a lane is the order of the list, as in the web app. Nothing else of the note
		changes, not even updatedAt. True when the order changed."""
		note = self._need(self.getNote(noteId))
		other = self._need(self.getNote(otherId))
		if note is other:
			return False
		notes = self.notes
		# By identity: comparing whole notes would be slow with many notes.
		i = next(k for k, n in enumerate(notes) if n is note)
		j = next(k for k, n in enumerate(notes) if n is other)
		if i == (j + 1 if after else j - 1):
			return False
		if (j > i) == after and abs(j - i) == 1:
			# Side by side: a swap is enough.
			notes[i], notes[j] = other, note
		else:
			del notes[i]
			j = j - 1 if j > i else j
			notes.insert(j + 1 if after else j, note)
		self.save()
		return True

	def location(self, notebookId=None, folderId=None):
		"""Valid (notebookId, folderId) of a note: a notebook (its folder comes from the
		notebook), a folder directly, or neither (loose note)."""
		if notebookId is not None and self.getNotebook(notebookId) is not None:
			return notebookId, None
		if folderId is not None and self.getFolder(folderId) is not None:
			return None, folderId
		return None, None

	def moveNoteTo(self, noteId, notebookId=None, folderId=None):
		"""Moves the note to a notebook, to a folder or out of both. True when it changed."""
		notebookId, folderId = self.location(notebookId, folderId)
		return self.updateNote(noteId, notebookId=notebookId, folderId=folderId)

	def moveNoteToNotebook(self, noteId, notebookId):
		return self.moveNoteTo(noteId, notebookId=notebookId)

	def notesInFolder(self, folderId):
		"""Notes put directly in a folder (not in one of its notebooks)."""
		return [n for n in self.notes if n["folderId"] == folderId and n["notebookId"] is None]

	def placeCounts(self):
		"""Numbers of notes by place in one pass: ({notebookId: n}, {folderId: n directly}, loose)."""
		byNotebook = {}
		byFolder = {}
		loose = 0
		for n in self.notes:
			if n["notebookId"] is not None:
				byNotebook[n["notebookId"]] = byNotebook.get(n["notebookId"], 0) + 1
			elif n["folderId"] is not None:
				byFolder[n["folderId"]] = byFolder.get(n["folderId"], 0) + 1
			else:
				loose += 1
		return byNotebook, byFolder, loose

	def looseNotes(self):
		return [n for n in self.notes if n["notebookId"] is None and n["folderId"] is None]

	# -- folders ------------------------------------------------------------------------------

	def addFolder(self, name):
		name = model.cleanText(name, model.MAX_NAME)
		if not name:
			raise StoreError("emptyName")
		folder = {
			"id": model.newId(),
			"name": name,
			"color": model.FOLDER_COLORS[len(self.folders) % len(model.FOLDER_COLORS)],
			"createdAt": model.nowIso(),
		}
		self.folders.append(folder)
		self.save()
		return folder

	def renameFolder(self, folderId, name):
		folder = self._need(self.getFolder(folderId), "folder")
		name = model.cleanText(name, model.MAX_NAME)
		if not name:
			raise StoreError("emptyName")
		folder["name"] = name
		self.save()

	def deleteFolder(self, folderId):
		"""Notebooks and notes of the folder become loose (nothing is deleted)."""
		folder = self._need(self.getFolder(folderId), "folder")
		self.folders.remove(folder)
		for nb in self.notebooks:
			if nb["folderId"] == folderId:
				nb["folderId"] = None
		for note in self.notes:
			if note["folderId"] == folderId:
				note["folderId"] = None
		self.save()

	# -- notebooks ----------------------------------------------------------------------------

	def addNotebook(self, name, folderId=None):
		name = model.cleanText(name, model.MAX_NAME)
		if not name:
			raise StoreError("emptyName")
		if folderId is not None and self.getFolder(folderId) is None:
			folderId = None
		notebook = {
			"id": model.newId(),
			"name": name,
			"color": model.NOTEBOOK_COLORS[len(self.notebooks) % len(model.NOTEBOOK_COLORS)],
			"folderId": folderId,
			"createdAt": model.nowIso(),
		}
		self.notebooks.append(notebook)
		self.save()
		return notebook

	def renameNotebook(self, notebookId, name):
		notebook = self._need(self.getNotebook(notebookId), "notebook")
		name = model.cleanText(name, model.MAX_NAME)
		if not name:
			raise StoreError("emptyName")
		notebook["name"] = name
		self.save()

	def moveNotebookToFolder(self, notebookId, folderId):
		notebook = self._need(self.getNotebook(notebookId), "notebook")
		if folderId is not None:
			self._need(self.getFolder(folderId), "folder")
		notebook["folderId"] = folderId
		self.save()

	def deleteNotebook(self, notebookId):
		"""The notes of the notebook become loose (nothing is deleted)."""
		notebook = self._need(self.getNotebook(notebookId), "notebook")
		self.notebooks.remove(notebook)
		for note in self.notes:
			if note["notebookId"] == notebookId:
				note["notebookId"] = None
		self.save()
