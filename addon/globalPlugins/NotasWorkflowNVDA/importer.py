# -*- coding: UTF-8 -*-
# NotasWorkflowNVDA - importer.py
# Reads the text of a document (Word .docx, PowerPoint .pptx, text .txt, HTML page or e-mail
# .eml) as the light markup of the editor: headings, lists, bold, italic and strikethrough are
# kept; images are not; a table row becomes one line "a | b | c". Used to create a note from a
# document and to insert a document in a note. Standard library only; no wx and no NVDA
# modules here (the labels already come translated).
# Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
# This file is covered by the GNU General Public License, version 2.

import email
import email.policy
import os
import posixpath
import re
import zipfile
from email.utils import parsedate_to_datetime
# defusedxml is not part of NVDA: _Package.xml refuses any DTD (so no entity can be declared or
# expanded) before parsing, and expat never loads external files.
from xml.etree import ElementTree  # nosec B405

from . import markup, model

#: Extensions that can be read (the old binary .doc, .ppt and .rtf cannot, nor .msg and .pdf).
EXTENSIONS = (".docx", ".pptx", ".txt", ".html", ".htm", ".eml")
#: Largest file read.
MAX_FILE = 50 * 1024 * 1024
#: Largest part of a .docx or .pptx once uncompressed, and all the parts read together
#: (a "zip bomb" is refused instead of filling the memory).
MAX_PART = 100 * 1024 * 1024
MAX_UNZIPPED = 300 * 1024 * 1024

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
_P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
_DC = "{http://purl.org/dc/elements/1.1/}"
_NOTES_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide"

_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\ud800-\udfff]")
_SPACES_RE = re.compile(r"[ \t  -​  　]+")
_META_CHARSET_RE = re.compile(rb"""<meta[^>]+charset\s*=\s*["']?([A-Za-z0-9_.:-]+)""", re.I)
_HTML_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_HEADING_STYLE_RE = re.compile(r"^heading\s*([1-6])$")
#: Bullet characters typed or written by Word in a page or a text: the line becomes a list item.
_BULLET_CHAR_RE = re.compile("^[·•▪◦●■§] ")
_FALSE = ("0", "false", "off")


class DocumentError(Exception):
	"""kind: unsupported, tooBig, unreadable, damaged or empty."""

	def __init__(self, kind):
		super().__init__(kind)
		self.kind = kind


DEFAULT_LABELS = {
	"slide": "Slide {number}",
	"slideTitled": "Slide {number}: {title}",
	"notes": "Speaker notes:",
	"from": "From:",
	"to": "To:",
	"cc": "Cc:",
	"date": "Date:",
	"attachments": "Attachments:",
}


def canRead(path):
	return os.path.splitext(path)[1].lower() in EXTENSIONS


def readDocument(path, labels=None, formatDate=None):
	"""(title, text) of a document: the title of the document (or the subject of the e-mail),
	otherwise the file name; text in the light markup of the editor. Raises DocumentError."""
	labels = dict(DEFAULT_LABELS, **(labels or {}))
	ext = os.path.splitext(path)[1].lower()
	if ext not in EXTENSIONS:
		raise DocumentError("unsupported")
	try:
		if os.path.getsize(path) > MAX_FILE:
			raise DocumentError("tooBig")
		with open(path, "rb") as f:
			data = f.read(MAX_FILE + 1)
	except OSError:
		raise DocumentError("unreadable")
	if len(data) > MAX_FILE:
		raise DocumentError("tooBig")
	try:
		if ext == ".docx":
			title, text = _docx(data)
		elif ext == ".pptx":
			title, text = _pptx(data, labels)
		elif ext == ".eml":
			title, text = _eml(data, labels, formatDate)
		elif ext == ".txt":
			title, text = "", _decode(data)
		else:
			title, text = _html(data)
	except DocumentError:
		raise
	except (zipfile.BadZipFile, zipfile.LargeZipFile, ElementTree.ParseError, KeyError, ValueError, RuntimeError, EOFError, LookupError):
		# A damaged file, a file protected by a password (an encrypted .docx is not a zip)...
		raise DocumentError("damaged")
	text = tidy(text)
	if not text.strip():
		raise DocumentError("empty")
	title = model.cleanText(_CONTROL_RE.sub("", title or ""), model.MAX_TITLE)
	if not title:
		title = model.cleanText(os.path.splitext(os.path.basename(path))[0], model.MAX_TITLE)
	return title, text


def tidy(text):
	"""One space between words, no control characters, no blank lines (each line is already a
	paragraph), bullet characters as list items. Code blocks keep their spaces and lines."""
	out = []
	inCode = False
	for line in _CONTROL_RE.sub("", text.replace("\r\n", "\n").replace("\r", "\n")).split("\n"):
		if line.strip() == "```":
			inCode = not inCode
			out.append("```")
			continue
		if not inCode:
			line = _BULLET_CHAR_RE.sub("- ", _SPACES_RE.sub(" ", line).strip())
			if not line:
				continue
		out.append(line.rstrip())
	while out and not out[-1]:
		out.pop()
	return "\n".join(out)


def fitContent(text, limit=model.MAX_CONTENT):
	"""(text, cut): the text, or its first lines, so that the note (HTML) is at most limit.
	cut is True when something was left out."""
	if limit <= 0:
		return "", bool(text)
	if len(markup.textToHtml(text)) <= limit:
		return text, False
	lines = text.split("\n")
	low, high = 0, len(lines)
	# Binary search on the number of lines that fit.
	while low < high:
		middle = (low + high + 1) // 2
		if len(markup.textToHtml("\n".join(lines[:middle]))) <= limit:
			low = middle
		else:
			high = middle - 1
	if low == 0:
		# A single line longer than the limit: its beginning (escaping can make it 6 times longer).
		return lines[0][:limit // 6], True
	return "\n".join(lines[:low]), True


# -- text and HTML -------------------------------------------------------------------------------------

def _decode(data, declared=None):
	if data.startswith(b"\xef\xbb\xbf"):
		return data[3:].decode("utf-8", "replace")
	if data.startswith((b"\xff\xfe", b"\xfe\xff")):
		return data.decode("utf-16", "replace")
	for encoding in (declared, "utf-8"):
		if not encoding:
			continue
		try:
			return data.decode(encoding)
		except (UnicodeDecodeError, LookupError):
			pass
	return data.decode("cp1252", "replace")


def _html(data):
	match = _META_CHARSET_RE.search(data[:4096])
	source = _decode(data, match.group(1).decode("ascii") if match else None)
	return _htmlTitle(source), markup.htmlToText(source)


def _htmlTitle(source):
	match = _HTML_TITLE_RE.search(source[:20000])
	return markup.plainText(match.group(1)) if match else ""


# -- Office documents (.docx, .pptx) ------------------------------------------------------------------

class _Package:
	"""The parts of a .docx or .pptx, read with limits."""

	def __init__(self, data):
		import io

		self.zip = zipfile.ZipFile(io.BytesIO(data))
		self.names = set(self.zip.namelist())
		self.total = 0

	def read(self, name):
		info = self.zip.getinfo(name)
		if info.file_size > MAX_PART:
			raise DocumentError("tooBig")
		with self.zip.open(info) as f:
			data = f.read(MAX_PART + 1)
		self.total += len(data)
		if len(data) > MAX_PART or self.total > MAX_UNZIPPED:
			raise DocumentError("tooBig")
		return data

	def xml(self, name, required=True):
		if name not in self.names:
			if required:
				raise DocumentError("damaged")
			return None
		data = self.read(name)
		# Office parts never have a DTD: refusing one avoids entity expansion attacks.
		if b"<!DOCTYPE" in data or b"<!ENTITY" in data:
			raise DocumentError("damaged")
		return ElementTree.fromstring(data)  # nosec B314 - DTD refused above

	def title(self):
		core = self.xml("docProps/core.xml", required=False)
		node = core.find(_DC + "title") if core is not None else None
		return (node.text or "") if node is not None else ""

	def relations(self, part):
		"""{id: (type, part name)} of the relationships of a part."""
		folder, name = posixpath.split(part)
		rels = self.xml(posixpath.join(folder, "_rels", name + ".rels"), required=False)
		out = {}
		if rels is None:
			return out
		for rel in rels.iter(_REL + "Relationship"):
			target = rel.get("Target") or ""
			if rel.get("TargetMode") == "External":
				continue
			out[rel.get("Id")] = (rel.get("Type") or "", posixpath.normpath(posixpath.join(folder, target)).lstrip("/"))
		return out


def _runsText(runs):
	"""Light markup of [(text, marks)]: the same marks side by side are joined, and the marks
	go around the words only (spaces stay outside)."""
	joined = []
	for text, marks in runs:
		if joined and joined[-1][1] == marks:
			joined[-1][0] += text
		else:
			joined.append([text, marks])
	out = []
	for text, marks in joined:
		core = text.strip()
		if not marks or not core or "\n" in core:
			out.append(text)
			continue
		lead = text[:len(text) - len(text.lstrip())]
		trail = text[len(text.rstrip()):]
		# Bold and italic together would be "***", which the editor reads wrongly: bold wins.
		inner = "**" if "**" in marks else ("*" if "*" in marks else "")
		outer = "~~" if "~~" in marks else ""
		out.append(lead + outer + inner + core + inner + outer + trail)
	return "".join(out)


def _on(props, tag):
	node = props.find(tag) if props is not None else None
	return node is not None and (node.get(_W + "val") or "1").lower() not in _FALSE


class _Docx:
	def __init__(self, package):
		self.package = package
		self.styles = {}
		styles = package.xml("word/styles.xml", required=False)
		if styles is not None:
			for style in styles.iter(_W + "style"):
				name = style.find(_W + "name")
				based = style.find(_W + "basedOn")
				ppr = style.find(_W + "pPr")
				outline = ppr.find(_W + "outlineLvl") if ppr is not None else None
				num = ppr.find(_W + "numPr") if ppr is not None else None
				self.styles[style.get(_W + "styleId")] = {
					"name": (name.get(_W + "val") or "").lower() if name is not None else "",
					"based": based.get(_W + "val") if based is not None else None,
					"outline": outline.get(_W + "val") if outline is not None else None,
					"num": num,
				}
		self.formats = {}
		numbering = package.xml("word/numbering.xml", required=False)
		if numbering is not None:
			abstract = {}
			for node in numbering.iter(_W + "abstractNum"):
				levels = {}
				for lvl in node.iter(_W + "lvl"):
					fmt = lvl.find(_W + "numFmt")
					levels[lvl.get(_W + "ilvl")] = fmt.get(_W + "val") if fmt is not None else "decimal"
				abstract[node.get(_W + "abstractNumId")] = levels
			for num in numbering.iter(_W + "num"):
				ref = num.find(_W + "abstractNumId")
				if ref is not None:
					self.formats[num.get(_W + "numId")] = abstract.get(ref.get(_W + "val"), {})
		self.counters = {}

	def headingLevel(self, styleId, own):
		"""1-6 for a heading (style Title, heading 1-6, or an outline level), otherwise None."""
		if own is not None and own.isdigit() and int(own) < 6:
			return int(own) + 1
		for _depth in range(10):
			style = self.styles.get(styleId)
			if style is None:
				return None
			if style["name"] == "title":
				return 1
			match = _HEADING_STYLE_RE.match(style["name"])
			if match:
				return int(match.group(1))
			if style["outline"] is not None and style["outline"].isdigit() and int(style["outline"]) < 6:
				return int(style["outline"]) + 1
			styleId = style["based"]
		return None

	def listKind(self, numPr, styleId):
		"""("bullet" or "ordered", key of the counter), or None when the paragraph is not a list."""
		if numPr is None:
			style = self.styles.get(styleId)
			numPr = style["num"] if style else None
		if numPr is None:
			return None
		numId = numPr.find(_W + "numId")
		numId = numId.get(_W + "val") if numId is not None else None
		if not numId or numId == "0":
			return None
		ilvl = numPr.find(_W + "ilvl")
		ilvl = ilvl.get(_W + "val") if ilvl is not None else "0"
		fmt = self.formats.get(numId, {}).get(ilvl, "bullet")
		return ("bullet" if fmt in ("bullet", "none") else "ordered"), (numId, ilvl)

	def paragraphText(self, paragraph):
		runs = []
		for run in paragraph.iter(_W + "r"):
			props = run.find(_W + "rPr")
			marks = set()
			if _on(props, _W + "b"):
				marks.add("**")
			if _on(props, _W + "i"):
				marks.add("*")
			if _on(props, _W + "strike") or _on(props, _W + "dstrike"):
				marks.add("~~")
			marks = frozenset(marks)
			for child in run:
				if child.tag == _W + "t":
					runs.append((child.text or "", marks))
				elif child.tag in (_W + "tab", _W + "ptab"):
					runs.append((" ", marks))
				elif child.tag in (_W + "br", _W + "cr"):
					runs.append(("\n", frozenset()))
				elif child.tag == _W + "noBreakHyphen":
					runs.append(("-", marks))
		return _runsText(runs)

	def paragraph(self, node):
		ppr = node.find(_W + "pPr")
		styleId = None
		own = None
		numPr = None
		if ppr is not None:
			style = ppr.find(_W + "pStyle")
			styleId = style.get(_W + "val") if style is not None else None
			outline = ppr.find(_W + "outlineLvl")
			own = outline.get(_W + "val") if outline is not None else None
			numPr = ppr.find(_W + "numPr")
		text = self.paragraphText(node).strip()
		if not text:
			return []
		level = self.headingLevel(styleId, own)
		if level:
			return ["#" * level + " " + " ".join(text.split("\n"))]
		kind = self.listKind(numPr, styleId)
		lines = text.split("\n")
		if kind is None:
			return lines
		if kind[0] == "bullet":
			return ["- " + lines[0]] + lines[1:]
		number = self.counters[kind[1]] = self.counters.get(kind[1], 0) + 1
		return ["%d. %s" % (number, lines[0])] + lines[1:]

	def table(self, node):
		lines = []
		for row in node.iter(_W + "tr"):
			cells = []
			for cell in row.findall(_W + "tc"):
				parts = [" ".join(self.paragraphText(p).split()) for p in cell.iter(_W + "p")]
				cells.append(" ".join(p for p in parts if p))
			if any(cells):
				lines.append(" | ".join(cells))
		return lines

	def blocks(self, parent):
		lines = []
		for node in parent:
			if node.tag == _W + "p":
				lines += self.paragraph(node)
			elif node.tag == _W + "tbl":
				lines += self.table(node)
			elif node.tag in (_W + "sdt", _W + "sdtContent", _W + "customXml", _W + "smartTag", _W + "ins"):
				lines += self.blocks(node)
		return lines


def _docx(data):
	package = _Package(data)
	document = package.xml("word/document.xml")
	body = document.find(_W + "body")
	if body is None:
		raise DocumentError("damaged")
	return package.title(), "\n".join(_Docx(package).blocks(body))


def _pptParagraph(paragraph):
	runs = []
	for node in paragraph:
		if node.tag in (_A + "r", _A + "fld"):
			props = node.find(_A + "rPr")
			marks = set()
			if props is not None:
				if (props.get("b") or "0") not in _FALSE:
					marks.add("**")
				if (props.get("i") or "0") not in _FALSE:
					marks.add("*")
				if props.get("strike") not in (None, "noStrike"):
					marks.add("~~")
			text = node.find(_A + "t")
			runs.append(((text.text or "") if text is not None else "", frozenset(marks)))
		elif node.tag == _A + "br":
			runs.append(("\n", frozenset()))
	return _runsText(runs).strip()


def _pptBody(body, bullets):
	"""Lines of a text body; bullets: placeholder of a slide body (bulleted unless buNone)."""
	lines = []
	counters = {}
	for paragraph in body.findall(_A + "p"):
		text = _pptParagraph(paragraph)
		if not text:
			continue
		props = paragraph.find(_A + "pPr")
		level = props.get("lvl", "0") if props is not None else "0"
		if props is not None and props.find(_A + "buAutoNum") is not None:
			counters[level] = counters.get(level, 0) + 1
			prefix = "%d. " % counters[level]
		elif (props is not None and props.find(_A + "buChar") is not None) or (bullets and (props is None or props.find(_A + "buNone") is None)):
			prefix = "- "
		else:
			prefix = ""
		parts = text.split("\n")
		lines.append(prefix + parts[0])
		lines += parts[1:]
	return lines


def _pptShapes(tree, notes=False):
	"""(title, lines) of the shapes of a slide (or of its speaker notes), in their order."""
	title = []
	lines = []
	for shape in tree:
		if shape.tag == _P + "grpSp":
			subTitle, subLines = _pptShapes(shape, notes)
			title += subTitle
			lines += subLines
		elif shape.tag == _P + "sp":
			body = shape.find(_P + "txBody")
			if body is None:
				continue
			placeholder = shape.find("%snvSpPr/%snvPr/%sph" % (_P, _P, _P))
			kind = placeholder.get("type") if placeholder is not None else None
			if kind in ("title", "ctrTitle"):
				title += [" ".join(_pptParagraph(p).split()) for p in body.findall(_A + "p")]
			elif kind in ("sldNum", "dt", "ftr", "hdr", "sldImg"):
				continue
			else:
				bullets = not notes and placeholder is not None and kind in (None, "body", "obj")
				lines += _pptBody(body, bullets)
		elif shape.tag == _P + "graphicFrame":
			for table in shape.iter(_A + "tbl"):
				for row in table.iter(_A + "tr"):
					cells = [" ".join(" ".join(_pptParagraph(p).split()) for p in cell.iter(_A + "p")).strip() for cell in row.findall(_A + "tc")]
					if any(cells):
						lines.append(" | ".join(cells))
	return [t for t in title if t], lines


def _pptx(data, labels):
	package = _Package(data)
	presentation = package.xml("ppt/presentation.xml")
	relations = package.relations("ppt/presentation.xml")
	slides = []
	order = presentation.find(_P + "sldIdLst")
	if order is not None:
		for slide in order.findall(_P + "sldId"):
			rel = relations.get(slide.get(_R + "id"))
			if rel and rel[1] in package.names:
				slides.append(rel[1])
	if not slides:
		found = [n for n in package.names if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
		slides = sorted(found, key=lambda n: int(re.search(r"(\d+)\.xml$", n).group(1)))
	out = []
	for number, part in enumerate(slides, 1):
		slide = package.xml(part)
		tree = slide.find("%scSld/%sspTree" % (_P, _P))
		title, lines = _pptShapes(tree) if tree is not None else ([], [])
		if title:
			out.append("## " + labels["slideTitled"].format(number=number, title=" ".join(title)))
		else:
			out.append("## " + labels["slide"].format(number=number))
		out += lines
		for kind, target in package.relations(part).values():
			if kind != _NOTES_REL or target not in package.names:
				continue
			notes = package.xml(target)
			notesTree = notes.find("%scSld/%sspTree" % (_P, _P))
			_title, noteLines = _pptShapes(notesTree, notes=True) if notesTree is not None else ([], [])
			noteLines = [line for line in noteLines if line.strip()]
			if noteLines:
				out.append(labels["notes"])
				out += ["> " + line for line in noteLines]
	return package.title(), "\n".join(out)


# -- e-mail (.eml) --------------------------------------------------------------------------------------

def _eml(data, labels, formatDate):
	message = email.message_from_bytes(data, policy=email.policy.default)
	lines = []
	for key, header in (("from", "From"), ("to", "To"), ("cc", "Cc")):
		value = message.get(header)
		if value:
			lines.append("**%s** %s" % (labels[key], " ".join(str(value).split())))
	date = message.get("Date")
	if date:
		try:
			when = parsedate_to_datetime(str(date))
			shown = formatDate(when) if formatDate else when.isoformat(" ")
		except (TypeError, ValueError, IndexError):
			shown = str(date)
		lines.append("**%s** %s" % (labels["date"], shown))
	attachments = []
	for part in message.iter_attachments():
		name = part.get_filename()
		if name:
			attachments.append(" ".join(name.split()))
	if attachments:
		lines.append("**%s** %s" % (labels["attachments"], ", ".join(attachments)))
	body = message.get_body(preferencelist=("html", "plain"))
	if body is not None:
		try:
			content = body.get_content()
		except (LookupError, ValueError, AssertionError):
			raw = body.get_payload(decode=True) or b""
			content = _decode(raw, body.get_content_charset())
		if isinstance(content, bytes):
			content = _decode(content, body.get_content_charset())
		if lines:
			lines.append("---")
		lines.append(markup.htmlToText(content) if body.get_content_subtype() == "html" else content)
	subject = message.get("Subject")
	return (" ".join(str(subject).split()) if subject else ""), "\n".join(lines)
