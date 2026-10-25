# -*- coding: UTF-8 -*-
# NotasWorkflowNVDA - markup.py
# The note content is stored as HTML (paragraphs, headings, lists, quotes). Here it is
# edited as plain text with a light markup, converted both ways without loss.
# No wx and no NVDA modules here.
# Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
# This file is covered by the GNU General Public License, version 2.

import html
import re
from html.parser import HTMLParser

_HEADING_RE = re.compile(r"^(#{1,6}) (.*)$")
_BULLET_RE = re.compile(r"^[-*] (.*)$")
_ORDERED_RE = re.compile(r"^(\d{1,9})\. (.*)$")
_QUOTE_RE = re.compile(r"^> ?(.*)$")
_RULE_RE = re.compile(r"^-{3,}$")
_FENCE = "```"

_CODE_SPAN_RE = re.compile(r"`([^`]+)`")
_BOLD_RE = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")
_STRIKE_RE = re.compile(r"~~(?=\S)(.+?)(?<=\S)~~")
# * only marks italics at the start and end of words: 2*3*4 stays as it is.
_ITALIC_RE = re.compile(r"(?<![\w*])\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?![\w*])")


def _inline(text):
	"""Escapes the text and turns the inline markup into HTML."""
	out = []
	pos = 0
	for m in _CODE_SPAN_RE.finditer(text):
		out.append(_emphasis(text[pos:m.start()]))
		out.append("<code>%s</code>" % html.escape(m.group(1), quote=False))
		pos = m.end()
	out.append(_emphasis(text[pos:]))
	return "".join(out)


def _emphasis(text):
	text = html.escape(text, quote=False)
	text = _BOLD_RE.sub(r"<strong>\1</strong>", text)
	text = _STRIKE_RE.sub(r"<s>\1</s>", text)
	return _ITALIC_RE.sub(r"<em>\1</em>", text)


def textToHtml(text):
	"""Light markup (what the editor shows) -> HTML (what is stored)."""
	if not text:
		return ""
	lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
	out = []
	i = 0
	while i < len(lines):
		line = lines[i]
		if line.strip() == _FENCE:
			code = []
			i += 1
			while i < len(lines) and lines[i].strip() != _FENCE:
				code.append(lines[i])
				i += 1
			i += 1
			out.append("<pre><code>%s</code></pre>" % html.escape("\n".join(code), quote=False))
			continue
		if _RULE_RE.match(line.strip()):
			out.append("<hr>")
			i += 1
			continue
		m = _HEADING_RE.match(line)
		if m:
			level = len(m.group(1))
			out.append("<h%d>%s</h%d>" % (level, _inline(m.group(2)), level))
			i += 1
			continue
		if _BULLET_RE.match(line):
			items = []
			while i < len(lines) and _BULLET_RE.match(lines[i]):
				items.append("<li><p>%s</p></li>" % _inline(_BULLET_RE.match(lines[i]).group(1)))
				i += 1
			out.append("<ul>%s</ul>" % "".join(items))
			continue
		m = _ORDERED_RE.match(line)
		if m:
			start = int(m.group(1))
			items = []
			while i < len(lines) and _ORDERED_RE.match(lines[i]):
				items.append("<li><p>%s</p></li>" % _inline(_ORDERED_RE.match(lines[i]).group(2)))
				i += 1
			attr = ' start="%d"' % start if start != 1 else ""
			out.append("<ol%s>%s</ol>" % (attr, "".join(items)))
			continue
		if _QUOTE_RE.match(line):
			paras = []
			while i < len(lines) and _QUOTE_RE.match(lines[i]):
				body = _QUOTE_RE.match(lines[i]).group(1)
				paras.append("<p>%s</p>" % _inline(body) if body else "<p></p>")
				i += 1
			out.append("<blockquote>%s</blockquote>" % "".join(paras))
			continue
		out.append("<p>%s</p>" % _inline(line) if line else "<p></p>")
		i += 1
	return "".join(out)


class _Converter(HTMLParser):
	"""Stored HTML -> light markup (plain=False) or text only (plain=True).
	Unknown tags become just their text; script and style are dropped."""

	_MARKS = {"strong": "**", "b": "**", "em": "*", "i": "*", "s": "~~", "strike": "~~", "del": "~~"}
	_SKIP = {"script", "style", "template", "head", "title", "iframe", "object", "noscript"}

	def __init__(self, plain):
		super().__init__(convert_charrefs=True)
		self.plain = plain
		self.lines = []
		self.buf = []
		self.prefix = ""
		self.lists = []
		self.quote = 0
		self.pre = False
		self.skip = 0
		#: Cells already written in the table row (a row becomes one line: "a | b | c").
		self.cells = None

	def emit(self):
		quote = "" if self.plain else "> " * self.quote
		self.lines.append(quote + self.prefix + "".join(self.buf))
		self.buf = []
		self.prefix = ""

	def flush(self):
		if self.buf:
			self.emit()

	def mark(self, text):
		if not self.plain:
			self.buf.append(text)

	def handle_starttag(self, tag, attrs):
		if tag in ("p", "div") and self.cells is not None:
			# Paragraphs inside a table cell stay on the line of the row.
			if self.buf and self.buf[-1] != " | ":
				self.buf.append(" ")
			return
		if tag in self._SKIP:
			self.skip += 1
			return
		if self.skip:
			return
		if tag in ("p", "div"):
			self.flush()
		elif len(tag) == 2 and tag[0] == "h" and tag[1] in "123456":
			self.flush()
			self.mark("#" * int(tag[1]) + " ")
		elif tag in ("ul", "ol"):
			self.flush()
			start = 1
			for name, value in attrs:
				if name == "start" and value and value.isdigit() and len(value) < 10:
					start = int(value)
			self.lists.append([tag, start - 1])
		elif tag == "li":
			self.flush()
			if self.lists and not self.plain:
				ctx = self.lists[-1]
				indent = "  " * (len(self.lists) - 1)
				if ctx[0] == "ol":
					ctx[1] += 1
					self.prefix = "%s%d. " % (indent, ctx[1])
				else:
					self.prefix = indent + "- "
		elif tag == "blockquote":
			self.flush()
			self.quote += 1
		elif tag == "pre":
			self.flush()
			if not self.plain:
				self.emitRaw(_FENCE)
			self.pre = True
		elif tag == "hr":
			self.flush()
			if not self.plain:
				self.emitRaw("---")
		elif tag == "br":
			self.emit()
		elif tag == "tr":
			self.flush()
			self.cells = 0
		elif tag in ("td", "th"):
			if self.cells:
				self.buf.append(" | ")
			self.cells = (self.cells or 0) + 1
		elif tag in self._MARKS:
			self.mark(self._MARKS[tag])
		elif tag == "code" and not self.pre:
			self.mark("`")

	def handle_startendtag(self, tag, attrs):
		self.handle_starttag(tag, attrs)
		if tag not in ("br", "hr"):
			self.handle_endtag(tag)

	def emitRaw(self, text):
		quote = "" if self.plain else "> " * self.quote
		self.lines.append(quote + text)

	def handle_endtag(self, tag):
		if tag in self._SKIP:
			self.skip = max(0, self.skip - 1)
			return
		if self.skip:
			return
		if tag in ("p", "div") or (len(tag) == 2 and tag[0] == "h" and tag[1] in "123456"):
			if self.cells is None:
				self.emit()
		elif tag == "tr":
			self.flush()
			self.cells = None
		elif tag == "li":
			if self.buf or self.prefix:
				self.emit()
		elif tag in ("ul", "ol"):
			self.flush()
			if self.lists:
				self.lists.pop()
		elif tag == "blockquote":
			self.flush()
			self.quote = max(0, self.quote - 1)
		elif tag == "pre":
			self.flush()
			if not self.plain:
				self.emitRaw(_FENCE)
			self.pre = False
		elif tag in self._MARKS:
			self.mark(self._MARKS[tag])
		elif tag == "code" and not self.pre:
			self.mark("`")

	def handle_data(self, data):
		if self.skip:
			return
		if self.pre:
			parts = data.replace("\r\n", "\n").split("\n")
			for n, part in enumerate(parts):
				if n:
					self.emit()
				self.buf.append(part)
			return
		self.buf.append(data.replace("\r", " ").replace("\n", " ").replace("\t", " "))

	def result(self):
		self.close()
		self.flush()
		return "\n".join(self.lines)


def _convert(content, plain):
	if not content:
		return ""
	if "<" not in content:
		# Plain text (for example, imported from another tool).
		return html.unescape(content).replace("\r\n", "\n")
	conv = _Converter(plain)
	try:
		conv.feed(content)
		return conv.result()
	except Exception:
		# html.parser never runs anything; anything it cannot parse is shown as text without tags.
		return re.sub(r"<[^>]*>", " ", content)


def htmlToText(content):
	"""Stored HTML -> light markup (shown in the editor)."""
	return _convert(content, plain=False)


def plainText(content):
	"""Only the words of the note, without markup (search, preview)."""
	return _convert(content, plain=True)


def preview(content, limit=100):
	"""One line with the first 100 characters of the note."""
	text = " ".join(plainText(content).split())
	return text[:limit]


# -- formatting of the editor ------------------------------------------------------------

INLINE_MARKS = {"bold": "**", "italic": "*", "strike": "~~", "code": "`"}
LINE_PREFIXES = {"heading2": "## ", "heading3": "### ", "bullet": "- ", "ordered": "1. ", "quote": "> "}
_LINE_PREFIX_RE = {
	"heading2": re.compile(r"^## "),
	"heading3": re.compile(r"^### "),
	"bullet": re.compile(r"^[-*] "),
	"ordered": re.compile(r"^\d{1,9}\. "),
	"quote": re.compile(r"^> ?"),
}
_ANY_HEADING_RE = re.compile(r"^#{1,6} ")
FORMATS = ("bold", "italic", "strike", "code", "heading2", "heading3", "bullet", "ordered", "quote", "divider")


def applyFormat(text, start, end, kind):
	"""Applies (or removes) a format to the selection [start, end) of text.

	Returns (newText, newStart, newEnd, applied): applied is False when the format was removed."""
	start, end = sorted((max(0, min(start, len(text))), max(0, min(end, len(text)))))
	if kind in INLINE_MARKS:
		return _inlineFormat(text, start, end, INLINE_MARKS[kind])
	if kind in LINE_PREFIXES:
		return _lineFormat(text, start, end, kind)
	if kind == "divider":
		before = "" if start == 0 or text[start - 1] == "\n" else "\n"
		after = "" if end < len(text) and text[end] == "\n" else "\n"
		insert = before + "---" + after
		pos = start + len(insert)
		return text[:start] + insert + text[end:], pos, pos, True
	raise ValueError(kind)


def _inlineFormat(text, start, end, mark):
	size = len(mark)
	if start == end:
		new = text[:start] + mark + mark + text[end:]
		return new, start + size, start + size, True
	sel = text[start:end]
	if len(sel) > 2 * size and sel.startswith(mark) and sel.endswith(mark):
		inner = sel[size:-size]
		return text[:start] + inner + text[end:], start, start + len(inner), False
	if text[max(0, start - size):start] == mark and text[end:end + size] == mark:
		return text[:start - size] + sel + text[end + size:], start - size, end - size, False
	new = text[:start] + mark + sel + mark + text[end:]
	return new, start + size, end + size, True


def _lineFormat(text, start, end, kind):
	lineStart = text.rfind("\n", 0, start) + 1
	lineEnd = text.find("\n", end)
	if lineEnd == -1:
		lineEnd = len(text)
	lines = text[lineStart:lineEnd].split("\n")
	pattern = _LINE_PREFIX_RE[kind]
	remove = all(pattern.match(line) for line in lines)
	out = []
	for n, line in enumerate(lines):
		if remove:
			out.append(pattern.sub("", line, count=1))
			continue
		if kind.startswith("heading"):
			line = _ANY_HEADING_RE.sub("", line, count=1)
		elif pattern.match(line):
			line = pattern.sub("", line, count=1)
		prefix = "%d. " % (n + 1) if kind == "ordered" else LINE_PREFIXES[kind]
		out.append(prefix + line)
	segment = "\n".join(out)
	new = text[:lineStart] + segment + text[lineEnd:]
	if start == end:
		pos = lineStart + len(out[0])
		return new, pos, pos, not remove
	return new, lineStart, lineStart + len(segment), not remove
