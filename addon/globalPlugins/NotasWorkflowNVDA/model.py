# -*- coding: UTF-8 -*-
# NotasWorkflowNVDA - model.py
# Data model of the add-on: notes, notebooks,
# folders and the four default lanes. No wx and no NVDA modules here.
# Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
# This file is covered by the GNU General Public License, version 2.

import datetime
import re
import uuid

#: The four status lanes, in order (the colour is kept in the file, never needed to use the add-on).
LANES = (
	{"id": "todo", "color": "#007AFF", "order": 0},
	{"id": "inprogress", "color": "#FF9500", "order": 1},
	{"id": "blocked", "color": "#FF2D55", "order": 2},
	{"id": "done", "color": "#34C759", "order": 3},
)
LANE_IDS = tuple(lane["id"] for lane in LANES)
DEFAULT_LANE = "todo"

#: Colours given in turn to new notebooks and folders.
NOTEBOOK_COLORS = ("#007AFF", "#34C759", "#FF9500", "#FF2D55", "#AF52DE", "#5856D6")
FOLDER_COLORS = ("#FF9500", "#5856D6", "#34C759", "#FF2D55", "#007AFF", "#AF52DE")

MAX_TITLE = 200
MAX_NAME = 100
MAX_TAG = 50
MAX_TAGS = 30
MAX_CONTENT = 1024 * 1024
MAX_ID = 64
#: Number of notes of "Recent notes".
RECENT_COUNT = 10

_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,%d}" % MAX_ID)
_COLOR_RE = re.compile(r"#[0-9A-Fa-f]{6}")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Filters of the main window.
FILTER_ALL = ("all", None)
FILTER_LOOSE = ("loose", None)
FILTER_RECENT = ("recent", None)


def newId():
	return str(uuid.uuid4())


def isValidId(value):
	return isinstance(value, str) and _ID_RE.fullmatch(value) is not None


def nowIso(now=None):
	"""The current time as JavaScript's Date.toISOString() writes it."""
	now = now or datetime.datetime.now(datetime.timezone.utc)
	now = now.astimezone(datetime.timezone.utc)
	return now.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (now.microsecond // 1000)


def parseIso(value):
	"""Datetime (aware) of an ISO date, or None."""
	if not isinstance(value, str) or len(value) > 40:
		return None
	text = value.strip()
	if text.endswith("Z"):
		text = text[:-1] + "+00:00"
	try:
		dt = datetime.datetime.fromisoformat(text)
	except ValueError:
		return None
	if dt.tzinfo is None:
		dt = dt.replace(tzinfo=datetime.timezone.utc)
	return dt


def _isoOr(value, fallback):
	return value if parseIso(value) is not None else fallback


def cleanText(value, limit):
	"""A single-line text: str only, no control characters, trimmed and limited."""
	if not isinstance(value, str):
		return ""
	value = _CONTROL_RE.sub("", value).replace("\r", " ").replace("\n", " ").replace("\t", " ")
	return value.strip()[:limit]


def cleanTags(tags):
	"""List of tags: text, no repetition (ignoring case), no empty one, limited."""
	if isinstance(tags, str):
		tags = tags.split(",")
	if not isinstance(tags, (list, tuple)):
		return []
	out = []
	seen = set()
	for tag in tags:
		tag = cleanText(tag, MAX_TAG)
		if tag and tag.casefold() not in seen:
			seen.add(tag.casefold())
			out.append(tag)
		if len(out) >= MAX_TAGS:
			break
	return out


def laneIndex(laneId):
	try:
		return LANE_IDS.index(laneId)
	except ValueError:
		return 0


def neighbourLane(laneId, step):
	"""Lane before (step -1) or after (step +1), or None at the ends."""
	i = laneIndex(laneId) + step
	if 0 <= i < len(LANE_IDS):
		return LANE_IDS[i]
	return None


def makeNote(title, laneId=DEFAULT_LANE, notebookId=None, folderId=None, content="", tags=(), now=None):
	stamp = nowIso(now)
	return {
		"id": newId(),
		"title": cleanText(title, MAX_TITLE),
		"content": content if isinstance(content, str) else "",
		"tags": cleanTags(list(tags)),
		"laneId": laneId if laneId in LANE_IDS else DEFAULT_LANE,
		"notebookId": notebookId,
		"folderId": folderId,
		"createdAt": stamp,
		"updatedAt": stamp,
	}


def sanitizeFolder(raw, now, defaultColor=FOLDER_COLORS[0]):
	if not isinstance(raw, dict) or not isValidId(raw.get("id")):
		return None
	name = cleanText(raw.get("name"), MAX_NAME)
	if not name:
		return None
	color = raw.get("color")
	return {
		"id": raw["id"],
		"name": name,
		"color": color if isinstance(color, str) and _COLOR_RE.fullmatch(color) else defaultColor,
		"createdAt": _isoOr(raw.get("createdAt"), now),
	}


def sanitizeNotebook(raw, now, folderIds):
	item = sanitizeFolder(raw, now, NOTEBOOK_COLORS[0])
	if item is None:
		return None
	folderId = raw.get("folderId")
	item["folderId"] = folderId if folderId in folderIds else None
	return item


def sanitizeNote(raw, now, notebookIds, folderIds):
	"""A valid note built from untrusted data (file or import), or None."""
	if not isinstance(raw, dict) or not isValidId(raw.get("id")):
		return None
	content = raw.get("content")
	if not isinstance(content, str) or len(content) > MAX_CONTENT:
		content = ""
	lane = raw.get("laneId")
	notebookId = raw.get("notebookId")
	folderId = raw.get("folderId")
	created = _isoOr(raw.get("createdAt"), now)
	return {
		"id": raw["id"],
		"title": cleanText(raw.get("title"), MAX_TITLE),
		"content": content,
		"tags": cleanTags(raw.get("tags")),
		"laneId": lane if lane in LANE_IDS else DEFAULT_LANE,
		"notebookId": notebookId if notebookId in notebookIds else None,
		"folderId": folderId if folderId in folderIds else None,
		"createdAt": created,
		"updatedAt": _isoOr(raw.get("updatedAt"), created),
	}


def updatedKey(note):
	dt = parseIso(note.get("updatedAt"))
	return dt.timestamp() if dt else 0.0


def filterNotes(notes, notebooks, activeFilter):
	"""Notes shown by a filter, in creation order (recent: last changed first).

	notes: list of notes; notebooks: list of notebooks; activeFilter: (kind, id) where kind
	is all, loose, recent, notebook or folder."""
	kind, ident = activeFilter
	if kind == "loose":
		# Loose: neither in a notebook nor directly in a folder.
		return [n for n in notes if n["notebookId"] is None and n["folderId"] is None]
	if kind == "recent":
		return sorted(notes, key=updatedKey, reverse=True)[:RECENT_COUNT]
	if kind == "notebook":
		return [n for n in notes if n["notebookId"] == ident]
	if kind == "folder":
		inFolder = {nb["id"] for nb in notebooks if nb["folderId"] == ident}
		return [n for n in notes if n["folderId"] == ident or n["notebookId"] in inFolder]
	return list(notes)


def byLane(notes):
	"""{laneId: [notes]} for the four lanes, keeping the order."""
	out = {lane: [] for lane in LANE_IDS}
	for note in notes:
		out.get(note["laneId"], out[DEFAULT_LANE]).append(note)
	return out
