# -*- coding: UTF-8 -*-
# NotasWorkflowNVDA - exporter.py
# Exports a note, a notebook or a folder as a Word (.docx), Markdown (.md) or HTML (.html)
# document, in one file or one file for each note. Standard library only; no wx and no NVDA
# modules here (the texts already come translated).
# Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
# This file is covered by the GNU General Public License, version 2.

import html
import os
import re
import zipfile
from html.parser import HTMLParser

from . import markup

FORMATS = ("docx", "md", "html")
EXTENSIONS = {"docx": ".docx", "md": ".md", "html": ".html"}

#: Characters that cannot be in an XML document (and so in a .docx), and lone surrogates
#: (a damaged file could have them; they cannot be written as UTF-8).
_BAD_CHARS_RE = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\ud800-\udfff]")
#: Characters Windows does not accept in a file name.
_BAD_NAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL"} | {"COM%d" % i for i in range(1, 10)} | {"LPT%d" % i for i in range(1, 10)}
MAX_NAME = 80
#: Fixed date inside the .docx zip: the same notes always give the same file.
_ZIP_DATE = (2026, 1, 1, 0, 0, 0)


def clean(text):
	return _BAD_CHARS_RE.sub("", text or "")


# -- blocks -------------------------------------------------------------------------------------------
# A document is a list of blocks, the same for the three formats:
#   {"kind": "h", "level": 1-6, "runs": runs}    heading
#   {"kind": "p", "runs": runs, "meta": bool}     paragraph (meta: status, tags and dates of a note)
#   {"kind": "li", "ordered": bool, "start": n, "list": id, "runs": runs}
#   {"kind": "quote", "runs": runs}
#   {"kind": "code", "text": text}
#   {"kind": "hr"}
# runs: [(text, frozenset of "bold", "italic", "strike", "code")]

def heading(level, text):
	return {"kind": "h", "level": max(1, min(6, level)), "runs": [(clean(text), frozenset())]}


def paragraph(text, meta=False):
	return {"kind": "p", "runs": [(clean(text), frozenset())], "meta": meta}


class _BlockParser(HTMLParser):
	"""The HTML written by markup.textToHtml (only safe tags) -> blocks. The headings of the
	content go below the heading of the note (level noteLevel): heading 1 and 2 of the content
	become noteLevel + 1, heading 3 noteLevel + 2, and so on."""

	_MARKS = {"strong": "bold", "em": "italic", "s": "strike", "code": "code"}

	def __init__(self, noteLevel, listIds):
		super().__init__(convert_charrefs=True)
		self.noteLevel = noteLevel
		self.listIds = listIds
		self.blocks = []
		self.current = None
		self.marks = set()
		self.lists = []
		self.quote = 0
		self.pre = False

	def _start(self, block):
		self._end()
		block.setdefault("runs", [])
		self.current = block

	def _end(self):
		if self.current is not None:
			block = self.current
			self.current = None
			if block["kind"] == "code" or any(text.strip() for text, _m in block["runs"]):
				self.blocks.append(block)

	def handle_starttag(self, tag, attrs):
		if tag == "pre":
			self._start({"kind": "code", "text": ""})
			self.pre = True
		elif tag == "p" or (len(tag) == 2 and tag[0] == "h" and tag[1] in "123456"):
			if tag != "p":
				self._start({"kind": "h", "level": min(6, max(self.noteLevel + 1, int(tag[1]) + self.noteLevel - 1))})
			elif self.lists:
				ordered, start, listId, counter = self.lists[-1]
				self._start({"kind": "li", "ordered": ordered, "start": start, "list": listId, "number": counter})
			elif self.quote:
				self._start({"kind": "quote"})
			else:
				self._start({"kind": "p", "meta": False})
		elif tag in ("ul", "ol"):
			start = 1
			for name, value in attrs:
				if name == "start" and value and value.isdigit() and len(value) < 10:
					start = int(value)
			self.listIds[0] += 1
			self.lists.append([tag == "ol", start, self.listIds[0], start - 1])
		elif tag == "li" and self.lists:
			self.lists[-1][3] += 1
		elif tag == "blockquote":
			self.quote += 1
		elif tag == "hr":
			self._end()
			self.blocks.append({"kind": "hr"})
		elif tag in self._MARKS and not self.pre:
			self.marks.add(self._MARKS[tag])

	def handle_endtag(self, tag):
		if tag == "pre":
			self.pre = False
			self._end()
		elif tag == "p" or (len(tag) == 2 and tag[0] == "h" and tag[1] in "123456"):
			self._end()
		elif tag in ("ul", "ol") and self.lists:
			self.lists.pop()
		elif tag == "blockquote":
			self.quote = max(0, self.quote - 1)
		elif tag in self._MARKS:
			self.marks.discard(self._MARKS[tag])

	def handle_data(self, data):
		data = clean(data)
		if self.current is None:
			if not data.strip():
				return
			self._start({"kind": "p", "meta": False})
		if self.current["kind"] == "code":
			self.current["text"] += data
		else:
			self.current["runs"].append((data, frozenset(self.marks)))

	def result(self):
		self.close()
		self._end()
		return self.blocks


def contentBlocks(content, noteLevel=1, listIds=None):
	"""Blocks of the content of a note (stored HTML). The content is first read as the
	editor shows it and written again as HTML: only the formats of the editor are kept,
	and nothing of an imported file (scripts, styles, links) reaches the export."""
	safe = markup.textToHtml(markup.htmlToText(content or ""))
	parser = _BlockParser(noteLevel, listIds if listIds is not None else [0])
	parser.feed(safe)
	return parser.result()


# -- documents -----------------------------------------------------------------------------------------

def noteBlocks(note, level, title, meta, listIds):
	"""Heading of the note, its meta paragraphs and its content."""
	blocks = [heading(level, title)]
	blocks += [paragraph(line, meta=True) for line in meta]
	blocks += contentBlocks(note.get("content"), level, listIds)
	return blocks


def buildDocument(title, intro, sections, describe, noteTitle):
	"""Blocks of one document.

	title: heading 1 of the document (None for a single note: the note is the heading 1).
	intro: paragraph after the title (or None).
	sections: [(heading or None, notes)]; a section with a heading puts its notes one level
	below it. describe(note) -> meta lines; noteTitle(note) -> title text."""
	blocks = []
	listIds = [0]
	level = 1
	if title is not None:
		blocks.append(heading(1, title))
		level = 2
	if intro:
		blocks.append(paragraph(intro))
	for sectionTitle, notes in sections:
		if not notes:
			continue
		noteLevel = level
		if sectionTitle is not None:
			blocks.append(heading(level, sectionTitle))
			noteLevel = level + 1
		for note in notes:
			blocks += noteBlocks(note, noteLevel, noteTitle(note), describe(note), listIds)
	return blocks


# -- Markdown -------------------------------------------------------------------------------------------

_MD_ESCAPE_RE = re.compile(r"([\\`*_~\[\]<>])")
_MD_LINE_START_RE = re.compile(r"^(\s*)(#|[-+]\s|\d+[.)]\s|>)")


def _mdText(text):
	return _MD_ESCAPE_RE.sub(r"\\\1", text)


def _mdRuns(runs):
	out = []
	for text, marks in runs:
		if not text:
			continue
		if "code" in marks:
			fence = "``" if "`" in text else "`"
			pad = " " if text.startswith("`") or text.endswith("`") else ""
			piece = "%s%s%s%s%s" % (fence, pad, text, pad, fence)
		else:
			if not text.strip():
				out.append(text)
				continue
			lead = text[:len(text) - len(text.lstrip())]
			trail = text[len(text.rstrip()):]
			core = _mdText(text.strip())
			if "bold" in marks:
				core = "**%s**" % core
			if "italic" in marks:
				core = "*%s*" % core
			if "strike" in marks:
				core = "~~%s~~" % core
			piece = lead + core + trail
		out.append(piece)
	line = "".join(out).replace("\n", " ").strip()
	m = _MD_LINE_START_RE.match(line)
	if m:
		# "1. " becomes "1\. " (a backslash before a digit is not an escape); the others get it before them.
		at = m.end(2) - 2 if m.group(2)[0].isdigit() else m.end(1)
		line = line[:at] + "\\" + line[at:]
	return line


def toMarkdown(blocks):
	parts = []
	prev = None
	for block in blocks:
		kind = block["kind"]
		if kind == "h":
			text = "%s %s" % ("#" * block["level"], _mdRuns(block["runs"]))
		elif kind == "li":
			marker = "%d." % block["number"] if block["ordered"] else "-"
			text = "%s %s" % (marker, _mdRuns(block["runs"]))
		elif kind == "quote":
			text = "> " + _mdRuns(block["runs"])
		elif kind == "code":
			fence = "````" if "```" in block["text"] else "```"
			text = "%s\n%s\n%s" % (fence, block["text"].rstrip("\n"), fence)
		elif kind == "hr":
			text = "---"
		else:
			text = _mdRuns(block["runs"])
		# Items of the same list (and lines of the same quote) stay together.
		together = prev is not None and (
			(kind == "li" and prev["kind"] == "li" and prev["list"] == block["list"])
			or (kind == "quote" and prev["kind"] == "quote")
		)
		if kind == "quote" and together:
			parts.append(">")
		elif parts and not together:
			parts.append("")
		parts.append(text)
		prev = block
	return "\n".join(parts) + "\n"


# -- HTML -----------------------------------------------------------------------------------------------

_HTML_TAGS = (("code", "code"), ("bold", "strong"), ("italic", "em"), ("strike", "s"))

_CSS = """body{font-family:Segoe UI,Arial,sans-serif;line-height:1.5;max-width:50em;margin:2em auto;padding:0 1em;color:#1a1a1a;background:#fff}
h1,h2,h3,h4,h5,h6{color:#1F4E79;line-height:1.25}
.meta{color:#444;margin:.2em 0}
blockquote{margin:1em 0;padding:.2em 1em;border-left:4px solid #1F4E79;background:#f3f6fa}
pre{background:#f4f4f4;padding:.8em;overflow-x:auto;white-space:pre-wrap}
code{font-family:Consolas,monospace}
@media (prefers-color-scheme:dark){body{color:#eee;background:#1e1e1e}h1,h2,h3,h4,h5,h6{color:#9cc3ea}.meta{color:#bbb}blockquote{background:#26303a}pre{background:#2a2a2a}}"""


def _htmlRuns(runs):
	out = []
	for text, marks in runs:
		piece = html.escape(text, quote=False)
		for mark, tag in _HTML_TAGS:
			if mark in marks:
				piece = "<%s>%s</%s>" % (tag, piece, tag)
		out.append(piece)
	return "".join(out)


def toHtml(blocks, title, lang):
	body = []
	openList = None
	inQuote = False
	for block in blocks:
		kind = block["kind"]
		if openList is not None and (kind != "li" or block["list"] != openList[1]):
			body.append("</%s>" % openList[0])
			openList = None
		if inQuote and kind != "quote":
			body.append("</blockquote>")
			inQuote = False
		if kind == "h":
			body.append("<h%d>%s</h%d>" % (block["level"], _htmlRuns(block["runs"]), block["level"]))
		elif kind == "li":
			if openList is None:
				tag = "ol" if block["ordered"] else "ul"
				start = ' start="%d"' % block["start"] if block["ordered"] and block["start"] != 1 else ""
				body.append("<%s%s>" % (tag, start))
				openList = (tag, block["list"])
			body.append("<li>%s</li>" % _htmlRuns(block["runs"]))
		elif kind == "quote":
			if not inQuote:
				body.append("<blockquote>")
				inQuote = True
			body.append("<p>%s</p>" % _htmlRuns(block["runs"]))
		elif kind == "code":
			body.append("<pre><code>%s</code></pre>" % html.escape(block["text"].rstrip("\n"), quote=False))
		elif kind == "hr":
			body.append("<hr>")
		else:
			cls = ' class="meta"' if block.get("meta") else ""
			body.append("<p%s>%s</p>" % (cls, _htmlRuns(block["runs"])))
	if openList is not None:
		body.append("</%s>" % openList[0])
	if inQuote:
		body.append("</blockquote>")
	return (
		'<!DOCTYPE html>\n<html lang="%s">\n<head>\n<meta charset="utf-8">\n'
		'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
		"<title>%s</title>\n<style>\n%s\n</style>\n</head>\n<body>\n<main>\n%s\n</main>\n</body>\n</html>\n"
	) % (html.escape(lang), html.escape(clean(title)), _CSS, "\n".join(body))


# -- Word -----------------------------------------------------------------------------------------------

_W_NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
_ACCENT = "1F4E79"


def _x(text):
	return html.escape(text, quote=True)


def _docxRuns(runs):
	out = []
	for text, marks in runs:
		if not text:
			continue
		props = ""
		if "bold" in marks:
			props += "<w:b/>"
		if "italic" in marks:
			props += "<w:i/>"
		if "strike" in marks:
			props += "<w:strike/>"
		if "code" in marks:
			props += '<w:rStyle w:val="CodeChar"/>'
		rpr = "<w:rPr>%s</w:rPr>" % props if props else ""
		out.append('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, _x(text)))
	return "".join(out)


def _para(style, content, extra=""):
	ppr = '<w:pPr><w:pStyle w:val="%s"/>%s</w:pPr>' % (style, extra) if style else ""
	return "<w:p>%s%s</w:p>" % (ppr, content)


def _docxBody(blocks):
	"""(paragraphs, numbered lists [(numId, start)]) of the document."""
	out = []
	numbered = []
	numOf = {}
	for block in blocks:
		kind = block["kind"]
		if kind == "h":
			out.append(_para("Heading%d" % block["level"], _docxRuns(block["runs"])))
		elif kind == "li":
			if block["ordered"]:
				if block["list"] not in numOf:
					numOf[block["list"]] = 2 + len(numbered)
					numbered.append((numOf[block["list"]], block["start"]))
				numId = numOf[block["list"]]
			else:
				numId = 1
			out.append(_para("ListParagraph", _docxRuns(block["runs"]), '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="%d"/></w:numPr>' % numId))
		elif kind == "quote":
			out.append(_para("Quote", _docxRuns(block["runs"])))
		elif kind == "code":
			lines = block["text"].rstrip("\n").split("\n")
			runs = "<w:r><w:br/></w:r>".join('<w:r><w:t xml:space="preserve">%s</w:t></w:r>' % _x(line) for line in lines)
			out.append(_para("CodeBlock", runs))
		elif kind == "hr":
			out.append(_para("Divider", ""))
		else:
			out.append(_para("Meta" if block.get("meta") else None, _docxRuns(block["runs"])))
	return out, numbered


def _stylesXml(lang):
	def pstyle(sid, name, ppr="", rpr="", outline=None):
		if outline is not None:
			ppr += '<w:outlineLvl w:val="%d"/>' % outline
		return (
			'<w:style w:type="paragraph" w:styleId="%s"><w:name w:val="%s"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
			"<w:pPr>%s</w:pPr><w:rPr>%s</w:rPr></w:style>"
		) % (sid, name, ppr, rpr)

	sizes = {1: 36, 2: 30, 3: 26, 4: 24, 5: 22, 6: 22}
	headings = "".join(
		pstyle(
			"Heading%d" % level, "heading %d" % level,
			'<w:keepNext/><w:spacing w:before="%d" w:after="120"/>' % (360 if level < 3 else 240),
			'<w:b/><w:color w:val="%s"/><w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (_ACCENT, sizes[level], sizes[level]),
			outline=level - 1,
		)
		for level in range(1, 7)
	)
	return (
		'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:styles %s>'
		'<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Calibri" w:cs="Calibri"/>'
		'<w:sz w:val="24"/><w:szCs w:val="24"/><w:lang w:val="%s" w:eastAsia="%s" w:bidi="%s"/></w:rPr></w:rPrDefault>'
		'<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="276" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
		'<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>'
		"%s%s%s%s%s%s"
		'<w:style w:type="character" w:styleId="CodeChar"><w:name w:val="Code Char"/><w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/></w:rPr></w:style>'
		"</w:styles>"
	) % (
		_W_NS, lang, lang, lang, headings,
		pstyle("Meta", "Note details", "", '<w:color w:val="404040"/>'),
		pstyle("ListParagraph", "List Paragraph", '<w:ind w:left="720"/><w:contextualSpacing/>'),
		pstyle("Quote", "Quote", '<w:ind w:left="567" w:right="567"/><w:pBdr><w:left w:val="single" w:sz="18" w:space="8" w:color="%s"/></w:pBdr>' % _ACCENT, "<w:i/>"),
		pstyle("CodeBlock", "Code", '<w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/><w:spacing w:after="120" w:line="240" w:lineRule="auto"/>', '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/><w:sz w:val="20"/>'),
		pstyle("Divider", "Divider", '<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="A6A6A6"/></w:pBdr>'),
	)


def _numberingXml(numbered):
	def abstract(aid, fmt, text, font=""):
		rpr = '<w:rPr><w:rFonts w:ascii="%s" w:hAnsi="%s" w:hint="default"/></w:rPr>' % (font, font) if font else ""
		return (
			'<w:abstractNum w:abstractNumId="%d"><w:multiLevelType w:val="singleLevel"/><w:lvl w:ilvl="0"><w:start w:val="1"/>'
			'<w:numFmt w:val="%s"/><w:lvlText w:val="%s"/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>%s</w:lvl></w:abstractNum>'
		) % (aid, fmt, text, rpr)

	nums = '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>'
	for numId, start in numbered:
		nums += (
			'<w:num w:numId="%d"><w:abstractNumId w:val="1"/><w:lvlOverride w:ilvl="0"><w:startOverride w:val="%d"/></w:lvlOverride></w:num>'
		) % (numId, start)
	return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:numbering %s>%s%s%s</w:numbering>' % (
		_W_NS, abstract(0, "bullet", "•", ),abstract(1, "decimal", "%1."), nums,
	)


_CONTENT_TYPES = (
	'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
	'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
	'<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
	'<Default Extension="xml" ContentType="application/xml"/>'
	'<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
	'<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
	'<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
	'<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
	'<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
	"</Types>"
)
_ROOT_RELS = (
	'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
	'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
	'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
	'<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
	'<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
	"</Relationships>"
)
_DOC_RELS = (
	'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
	'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
	'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
	'<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>'
	"</Relationships>"
)
_APP = (
	'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
	'<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Notas Workflow NVDA</Application></Properties>'
)


def _coreXml(title, lang):
	return (
		'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
		'<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
		'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
		'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
		"<dc:title>%s</dc:title><dc:language>%s</dc:language><dc:creator>Notas Workflow NVDA</dc:creator></cp:coreProperties>"
	) % (_x(clean(title)), _x(lang))


def writeDocx(path, blocks, title, lang):
	paragraphs, numbered = _docxBody(blocks)
	document = (
		'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:document %s><w:body>%s'
		'<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" '
		'w:header="567" w:footer="567" w:gutter="0"/></w:sectPr></w:body></w:document>'
	) % (_W_NS, "".join(paragraphs) or "<w:p/>")
	parts = (
		("[Content_Types].xml", _CONTENT_TYPES),
		("_rels/.rels", _ROOT_RELS),
		("word/document.xml", document),
		("word/_rels/document.xml.rels", _DOC_RELS),
		("word/styles.xml", _stylesXml(lang)),
		("word/numbering.xml", _numberingXml(numbered)),
		("docProps/core.xml", _coreXml(title, lang)),
		("docProps/app.xml", _APP),
	)
	with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
		for name, data in parts:
			info = zipfile.ZipInfo(name, _ZIP_DATE)
			info.compress_type = zipfile.ZIP_DEFLATED
			z.writestr(info, data.encode("utf-8"))


# -- files ----------------------------------------------------------------------------------------------

def writeDocument(path, fmt, blocks, title, lang):
	"""Writes the blocks in the format (docx, md or html). Raises OSError."""
	if fmt == "docx":
		writeDocx(path, blocks, title, lang)
		return
	text = toMarkdown(blocks) if fmt == "md" else toHtml(blocks, title, lang)
	with open(path, "w", encoding="utf-8", newline="\n") as f:
		f.write(text)


def safeName(text, fallback):
	"""A file or folder name Windows accepts, made from a title or a name."""
	name = _BAD_NAME_RE.sub("", clean(text)).strip()
	name = re.sub(r"\s+", " ", name)[:MAX_NAME].rstrip(". ")
	if not name:
		name = fallback
	if name.split(".")[0].upper() in _RESERVED_NAMES:
		name = "_" + name
	return name


def uniquePath(folder, name, ext, used):
	"""folder/name+ext, or folder/name (2)+ext... when that name exists or was already used.
	used: lower-case names already given in this folder (it is updated)."""
	candidate = name + ext
	n = 2
	while candidate.lower() in used or os.path.exists(os.path.join(folder, candidate)):
		candidate = "%s (%d)%s" % (name, n, ext)
		n += 1
	used.add(candidate.lower())
	return os.path.join(folder, candidate)


def writeSeparate(folder, rootName, fmt, groups, makeBlocks, noteTitle, lang, fallback):
	"""One file for each note, in a new folder called rootName inside folder (rootName (2)
	if it exists, so nothing is overwritten). groups: [(subfolder name or None, notes)]; the
	notes of a group with a name go in a subfolder with that name.
	Returns (the folder created, number of files written). Raises OSError."""
	ext = EXTENSIONS[fmt]
	root = uniquePath(folder, safeName(rootName, fallback), "", set())
	os.makedirs(root)
	subfolders = set()
	count = 0
	for groupName, notes in groups:
		if not notes:
			continue
		target = root
		if groupName is not None:
			target = uniquePath(root, safeName(groupName, fallback), "", subfolders)
			os.makedirs(target)
		used = set()
		for note in notes:
			title = noteTitle(note)
			path = uniquePath(target, safeName(title, fallback), ext, used)
			writeDocument(path, fmt, makeBlocks(note), title, lang)
			count += 1
	return root, count
