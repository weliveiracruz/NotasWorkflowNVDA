# -*- coding: UTF-8 -*-
# NotasWorkflowNVDA - search.py
# Text search of the notes, ignoring accents and case. The text of each note is
# prepared once and kept in an index until the note changes, so a search in
# 100,000 notes takes a fraction of a second. No wx and no NVDA modules here.
# Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
# This file is covered by the GNU General Public License, version 2.

import html
import re
import unicodedata

from .model import updatedKey

MAX_RESULTS = 100
EXCERPT_LENGTH = 120
MAX_QUERY = 200

# Combining marks (accents) left by NFKD: removed in one pass of the regex engine.
_MARKS = re.compile("[̀-ͯ᪰-᫿᷀-᷿⃐-⃿︠-︯]")
_SKIP = re.compile(r"<(script|style|template|noscript|iframe|object|head|title)\b[^>]*>.*?</\1\s*>", re.I | re.S)
_TAG = re.compile(r"<[^>]*>")
_SPACES = re.compile(r"\s+")


def _foldChar(ch):
	decomposed = unicodedata.normalize("NFKD", ch.casefold())
	return "".join(c for c in decomposed if not unicodedata.combining(c))


def fold(text):
	"""Lower case without accents: 'Ação' -> 'acao'."""
	return _MARKS.sub("", unicodedata.normalize("NFKD", text.casefold()))


def foldWithMap(text):
	"""(folded text, index in the original text of each folded character). Slower than
	fold(): used only for the excerpts of the results shown."""
	out = []
	positions = []
	for i, ch in enumerate(text):
		folded = _foldChar(ch)
		out.append(folded)
		positions.extend([i] * len(folded))
	return "".join(out), positions


def plainText(content):
	"""Words of the stored HTML for the search: tags, scripts and styles removed."""
	if not content:
		return ""
	if "<" in content:
		content = _TAG.sub(" ", _SKIP.sub(" ", content))
	return _SPACES.sub(" ", html.unescape(content)).strip()


def terms(query):
	return [t for t in fold((query or "")[:MAX_QUERY]).split() if t]


def excerpt(plain, query, maxLen=EXCERPT_LENGTH):
	"""Part of the text around the first term found."""
	plain = " ".join(plain.split())
	found = terms(query)
	if not found:
		return plain[:maxLen] + ("…" if len(plain) > maxLen else "")
	folded, positions = foldWithMap(plain)
	idx = next((i for i in (folded.find(t) for t in found) if i != -1), -1)
	if idx == -1:
		return plain[:maxLen] + ("…" if len(plain) > maxLen else "")
	idx = positions[idx]
	start = max(0, idx - 40)
	end = min(len(plain), idx + maxLen - 40)
	return ("…" if start > 0 else "") + plain[start:end] + ("…" if end < len(plain) else "")


class SearchIndex:
	"""Prepared text of each note (plain text, folded title and folded haystack).
	An entry is rebuilt only when the title, the content or the tags of the note change."""

	def __init__(self):
		self._entries = {}

	def entry(self, note):
		content = note.get("content", "")
		title = note.get("title", "")
		tags = tuple(note.get("tags", ()))
		cached = self._entries.get(note["id"])
		# "is" on the content: an edited note always gets a new string, so this is O(1).
		if cached is not None and cached[0] is content and cached[1] == title and cached[2] == tags:
			return cached
		plain = plainText(content)
		foldedTitle = fold(title)
		haystack = " ".join((foldedTitle, fold(plain), fold(" ".join(tags))))
		cached = (content, title, tags, plain, foldedTitle, haystack)
		self._entries[note["id"]] = cached
		return cached

	def forget(self, keep):
		"""Drops the entries of notes that no longer exist (keep: the ids that do)."""
		for noteId in [k for k in self._entries if k not in keep]:
			del self._entries[noteId]

	def __len__(self):
		return len(self._entries)


def search(notes, query, limit=MAX_RESULTS, index=None):
	"""[(note, score, excerpt)] best first. score = terms found / terms; ties: more
	terms in the title, then the note changed last."""
	wanted = terms(query)
	if not wanted:
		return []
	index = index if index is not None else SearchIndex()
	ranked = []
	for note in notes:
		haystack = index.entry(note)[5]
		hits = 0
		for t in wanted:
			if t in haystack:
				hits += 1
		if not hits:
			continue
		entry = index.entry(note)
		titleHits = sum(1 for t in wanted if t in entry[4])
		ranked.append((hits / len(wanted), titleHits, updatedKey(note), note, entry[3]))
	ranked.sort(key=lambda r: (r[0], r[1], r[2]), reverse=True)
	return [(note, score, excerpt(plain, query)) for score, _t, _u, note, plain in ranked[:limit]]
