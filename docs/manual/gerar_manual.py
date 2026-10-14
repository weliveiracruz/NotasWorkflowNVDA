# -*- coding: UTF-8 -*-
"""Gera o manual de uso em Word (docs/Manual-NotasWorkflowNVDA.docx) a partir de
docs/manual/MANUAL.md. Só biblioteca padrão do Python, como o resto do projeto.

Uso:  python docs/manual/gerar_manual.py   (o build.py também roda este script)

Markdown aceito: # título da capa, ## capítulos (Título 1 do Word), ### seções (Título 2), parágrafos, listas "- " e "1. ", tabelas,
citações "> " (caixa de destaque), **negrito**, `código` e ``código com `crase` ``.
{{versao}} vira a versão de addon/manifest.ini.

O documento é acessível: títulos com os estilos de título do Word (navegáveis
pelo leitor de telas), sumário com links, tabelas com linha de cabeçalho
repetida, idioma pt-BR e título nas propriedades. O SHA-256 do MANUAL.md fica
nas propriedades do arquivo para os testes saberem se o .docx está atualizado."""

import hashlib
import os
import re
import sys
import zipfile
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SOURCE = os.path.join(HERE, "MANUAL.md")
TARGET = os.path.join(ROOT, "docs", "Manual-NotasWorkflowNVDA.docx")
#: Data fixa dentro do zip: o .docx só muda quando o conteúdo muda.
ZIP_DATE = (2026, 1, 1, 0, 0, 0)
# A4 com margens de 2 cm.
PAGE_W, PAGE_H, MARGIN = 11906, 16838, 1134
TEXT_W = PAGE_W - 2 * MARGIN
ACCENT = "1F4E79"

W_NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'


def version():
	with open(os.path.join(ROOT, "addon", "manifest.ini"), encoding="utf-8") as f:
		return re.search(r"^version\s*=\s*(\S+)", f.read(), re.M).group(1)


def sourceHash(text):
	return hashlib.sha256(text.encode("utf-8")).hexdigest()


# -- inline -----------------------------------------------------------------------------------

_INLINE = re.compile(r"(``(.+?)``|`([^`]+)`|\*\*(.+?)\*\*)")


def runs(text, bold=False):
	"""Runs <w:r> of a line with **bold** and `code`."""
	out = []
	pos = 0
	for m in _INLINE.finditer(text):
		if m.start() > pos:
			out.append(_run(text[pos:m.start()], bold=bold))
		if m.group(4) is not None:
			out.append(_run(m.group(4), bold=True))
		else:
			code = m.group(2).strip() if m.group(2) is not None else m.group(3)
			out.append(_run(code, bold=bold, code=True))
		pos = m.end()
	if pos < len(text):
		out.append(_run(text[pos:], bold=bold))
	return "".join(out)


def _run(text, bold=False, code=False, style=None):
	# The character style comes first inside w:rPr (schema order).
	if code:
		style = "Codigo"
	props = ('<w:rStyle w:val="%s"/>' % style if style else "") + ("<w:b/>" if bold else "")
	rpr = "<w:rPr>%s</w:rPr>" % props if props else ""
	return '<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, escape(text))


def paragraph(content, style=None, extra=""):
	ppr = ""
	if style or extra:
		ppr = "<w:pPr>%s%s</w:pPr>" % ('<w:pStyle w:val="%s"/>' % style if style else "", extra)
	return "<w:p>%s%s</w:p>" % (ppr, content)


# -- blocks ----------------------------------------------------------------------------------------


class Builder:
	def __init__(self):
		self.body = []
		self.headings = []  # (level, text, bookmark)
		self.numbered = 0  # number of numbered lists (each restarts at 1)
		self.bookmark = 0

	def heading(self, level, text):
		self.bookmark += 1
		name = "_Secao%d" % self.bookmark
		self.headings.append((level, text, name))
		content = '<w:bookmarkStart w:id="%d" w:name="%s"/>%s<w:bookmarkEnd w:id="%d"/>' % (self.bookmark, name, runs(text), self.bookmark)
		# "#" is the title of the cover; "##" chapters are Word's Heading 1, "###" Heading 2,
		# so a screen reader navigates the chapters with the first heading level.
		self.body.append(paragraph(content, "Title" if level == 1 else "Heading%d" % (level - 1)))

	def text(self, line):
		self.body.append(paragraph(runs(line)))

	def bullets(self, items):
		for item in items:
			self.body.append(paragraph(runs(item), "ListParagraph", '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'))

	def ordered(self, items):
		self.numbered += 1
		numId = 1 + self.numbered
		for item in items:
			self.body.append(paragraph(runs(item), "ListParagraph", '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="%d"/></w:numPr>' % numId))

	def note(self, line):
		self.body.append(paragraph(runs(line), "Destaque"))

	def table(self, rows):
		cols = max(len(r) for r in rows)
		rows = [r + [""] * (cols - len(r)) for r in rows]
		# Widths proportional to the longest text of each column, with a minimum.
		lengths = [max(min(len(r[c]), 60) for r in rows) + 4 for c in range(cols)]
		widths = [max(1100, int(TEXT_W * n / sum(lengths))) for n in lengths]
		widths[-1] += TEXT_W - sum(widths)
		grid = "".join('<w:gridCol w:w="%d"/>' % w for w in widths)
		xml = [
			'<w:tbl><w:tblPr><w:tblStyle w:val="TabelaManual"/><w:tblW w:w="%d" w:type="dxa"/>'
			'<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>'
			"<w:tblGrid>%s</w:tblGrid>" % (TEXT_W, grid)
		]
		for n, row in enumerate(rows):
			header = n == 0
			trpr = "<w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>" if header else "<w:trPr><w:cantSplit/></w:trPr>"
			cells = []
			for c, value in enumerate(row):
				shade = '<w:shd w:val="clear" w:color="auto" w:fill="%s"/>' % ("DCE6F1" if header else "FFFFFF")
				cells.append(
					'<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/>%s</w:tcPr>%s</w:tc>'
					% (widths[c], shade, paragraph(runs(value, bold=header), "TextoTabela"))
				)
			xml.append("<w:tr>%s%s</w:tr>" % (trpr, "".join(cells)))
		xml.append("</w:tbl>")
		self.body.append("".join(xml))
		# Space after the table.
		self.body.append(paragraph("", "Espaco"))


def parse(md, builder):
	lines = md.splitlines()
	i = 0
	while i < len(lines):
		line = lines[i].rstrip()
		if not line.strip():
			i += 1
			continue
		m = re.match(r"^(#{1,3})\s+(.*)$", line)
		if m:
			builder.heading(len(m.group(1)), m.group(2).strip())
			i += 1
			continue
		if line.startswith("|"):
			rows = []
			while i < len(lines) and lines[i].startswith("|"):
				cells = _cells(lines[i])
				if not all(re.fullmatch(r":?-+:?", c) for c in cells):
					rows.append(cells)
				i += 1
			builder.table(rows)
			continue
		if re.match(r"^- ", line):
			items = []
			while i < len(lines) and re.match(r"^- ", lines[i]):
				items.append(lines[i][2:].strip())
				i += 1
			builder.bullets(items)
			continue
		if re.match(r"^\d+\. ", line):
			items = []
			while i < len(lines) and re.match(r"^\d+\. ", lines[i]):
				items.append(re.sub(r"^\d+\. ", "", lines[i]).strip())
				i += 1
			builder.ordered(items)
			continue
		if line.startswith("> "):
			builder.note(line[2:].strip())
			i += 1
			continue
		para = []
		while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||- |\d+\. |> )", lines[i]):
			para.append(lines[i].strip())
			i += 1
		builder.text(" ".join(para))


def _cells(line):
	"""Cells of a table row; | inside `code` does not split."""
	cells = []
	current = ""
	inCode = False
	for ch in line.strip().strip("|"):
		if ch == "`":
			inCode = not inCode
		if ch == "|" and not inCode:
			cells.append(current.strip())
			current = ""
		else:
			current += ch
	cells.append(current.strip())
	return cells


# -- document parts ------------------------------------------------------------------------------------


def documentXml(builder, ver):
	title = builder.headings[0][1] if builder.headings and builder.headings[0][0] == 1 else "Manual"
	cover = [
		paragraph(runs(title), "Title"),
		paragraph(runs("Manual de uso — versão %s" % ver), "Subtitle"),
		paragraph(runs("Complemento do NVDA com o mesmo fluxo da aplicação web Notas Workflow: folhas em raias de status, cadernos, pastas, edição com formatação, salvamento automático e busca.")),
		paragraph(runs("Sumário"), "TOCHeading"),
	]
	for level, text, name in builder.headings[1:]:
		if level != 2:
			continue
		link = '<w:hyperlink w:anchor="%s" w:history="1">%s</w:hyperlink>' % (name, _run(text, style="Hyperlink"))
		cover.append(paragraph(link, "TOC1"))
	cover.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
	# The first heading (the title) is already on the cover.
	body = builder.body[1:]
	sect = (
		'<w:sectPr><w:footerReference w:type="default" r:id="rIdFooter"/>'
		'<w:pgSz w:w="%d" w:h="%d"/><w:pgMar w:top="%d" w:right="%d" w:bottom="%d" w:left="%d" w:header="567" w:footer="567" w:gutter="0"/>'
		"</w:sectPr>" % (PAGE_W, PAGE_H, MARGIN, MARGIN, MARGIN, MARGIN)
	)
	return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:document %s><w:body>%s%s%s</w:body></w:document>' % (W_NS, "".join(cover), "".join(body), sect)


def stylesXml():
	def pstyle(sid, name, ppr="", rpr="", based="Normal", nxt="Normal", outline=None, extra=""):
		ol = '<w:outlineLvl w:val="%d"/>' % outline if outline is not None else ""
		return (
			'<w:style w:type="paragraph" w:styleId="%s"><w:name w:val="%s"/><w:basedOn w:val="%s"/><w:next w:val="%s"/>%s'
			"<w:pPr>%s%s</w:pPr><w:rPr>%s</w:rPr></w:style>" % (sid, name, based, nxt, extra, ppr, ol, rpr)
		)

	styles = [
		'<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Calibri" w:cs="Calibri"/>'
		'<w:sz w:val="23"/><w:szCs w:val="23"/><w:lang w:val="pt-BR" w:eastAsia="pt-BR" w:bidi="ar-SA"/></w:rPr></w:rPrDefault>'
		'<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="288" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>',
		'<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>',
		pstyle("Title", "Title", '<w:spacing w:before="2400" w:after="240"/>', '<w:b/><w:color w:val="%s"/><w:sz w:val="56"/><w:szCs w:val="56"/>' % ACCENT, extra="<w:qFormat/>"),
		pstyle("Subtitle", "Subtitle", '<w:spacing w:after="480"/>', '<w:color w:val="595959"/><w:sz w:val="32"/><w:szCs w:val="32"/>', extra="<w:qFormat/>"),
		pstyle("Heading1", "heading 1", '<w:keepNext/><w:keepLines/><w:spacing w:before="480" w:after="160"/><w:pBdr><w:bottom w:val="single" w:sz="8" w:space="4" w:color="%s"/></w:pBdr>' % ACCENT,
			'<w:b/><w:color w:val="%s"/><w:sz w:val="34"/><w:szCs w:val="34"/>' % ACCENT, outline=0, extra="<w:qFormat/>"),
		pstyle("Heading2", "heading 2", '<w:keepNext/><w:keepLines/><w:spacing w:before="320" w:after="120"/>', '<w:b/><w:color w:val="%s"/><w:sz w:val="28"/><w:szCs w:val="28"/>' % ACCENT, outline=1, extra="<w:qFormat/>"),
		pstyle("Heading3", "heading 3", '<w:keepNext/><w:keepLines/><w:spacing w:before="240" w:after="80"/>', '<w:b/><w:color w:val="404040"/><w:sz w:val="24"/><w:szCs w:val="24"/>', outline=2, extra="<w:qFormat/>"),
		pstyle("ListParagraph", "List Paragraph", '<w:spacing w:after="60"/><w:ind w:left="720"/>'),
		pstyle("Destaque", "Destaque", '<w:pBdr><w:left w:val="single" w:sz="24" w:space="8" w:color="%s"/></w:pBdr><w:shd w:val="clear" w:color="auto" w:fill="EAF1F8"/><w:spacing w:before="120" w:after="200"/><w:ind w:left="284" w:right="284"/>' % ACCENT),
		pstyle("TextoTabela", "Texto de tabela", '<w:spacing w:before="40" w:after="40" w:line="252" w:lineRule="auto"/>', '<w:sz w:val="21"/><w:szCs w:val="21"/>'),
		pstyle("Espaco", "Espaço depois de tabela", '<w:spacing w:after="80"/>', '<w:sz w:val="12"/>'),
		pstyle("TOCHeading", "TOC Heading", '<w:keepNext/><w:spacing w:before="240" w:after="160"/>', '<w:b/><w:color w:val="%s"/><w:sz w:val="30"/><w:szCs w:val="30"/>' % ACCENT),
		pstyle("TOC1", "toc 1", '<w:spacing w:before="60" w:after="20"/>', "<w:b/>"),
		pstyle("TOC2", "toc 2", '<w:spacing w:after="20"/><w:ind w:left="400"/>', ""),
		pstyle("Footer", "footer", '<w:jc w:val="center"/>', '<w:color w:val="595959"/><w:sz w:val="18"/>'),
		'<w:style w:type="character" w:styleId="Codigo"><w:name w:val="Código"/><w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/>'
		'<w:sz w:val="21"/><w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/></w:rPr></w:style>',
		'<w:style w:type="character" w:styleId="Hyperlink"><w:name w:val="Hyperlink"/><w:rPr><w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr></w:style>',
		'<w:style w:type="table" w:default="1" w:styleId="TableNormal"><w:name w:val="Normal Table"/><w:tblPr><w:tblInd w:w="0" w:type="dxa"/>'
		'<w:tblCellMar><w:top w:w="0" w:type="dxa"/><w:left w:w="108" w:type="dxa"/><w:bottom w:w="0" w:type="dxa"/><w:right w:w="108" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style>',
		'<w:style w:type="table" w:styleId="TabelaManual"><w:name w:val="Tabela do manual"/><w:basedOn w:val="TableNormal"/><w:tblPr><w:tblBorders>'
		+ "".join('<w:%s w:val="single" w:sz="4" w:space="0" w:color="A6A6A6"/>' % side for side in ("top", "left", "bottom", "right", "insideH", "insideV"))
		+ '</w:tblBorders><w:tblCellMar><w:top w:w="40" w:type="dxa"/><w:left w:w="100" w:type="dxa"/><w:bottom w:w="40" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style>',
	]
	return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:styles %s>%s</w:styles>' % (W_NS, "".join(styles))


def numberingXml(numberedLists):
	bullet = (
		'<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="singleLevel"/><w:lvl w:ilvl="0"><w:start w:val="1"/>'
		'<w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>'
		'<w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/></w:rPr></w:lvl></w:abstractNum>'
	)
	decimal = (
		'<w:abstractNum w:abstractNumId="1"><w:multiLevelType w:val="singleLevel"/><w:lvl w:ilvl="0"><w:start w:val="1"/>'
		'<w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum>'
	)
	nums = ['<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>']
	for n in range(numberedLists):
		nums.append('<w:num w:numId="%d"><w:abstractNumId w:val="1"/><w:lvlOverride w:ilvl="0"><w:startOverride w:val="1"/></w:lvlOverride></w:num>' % (n + 2))
	return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:numbering %s>%s%s%s</w:numbering>' % (W_NS, bullet, decimal, "".join(nums))


def footerXml(ver):
	field = lambda code: (  # noqa: E731
		'<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> %s </w:instrText></w:r>'
		'<w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>1</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r>' % code
	)
	content = _run("Notas Workflow NVDA %s — página " % ver) + field("PAGE") + _run(" de ") + field("NUMPAGES")
	return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:ftr %s>%s</w:ftr>' % (W_NS, paragraph(content, "Footer"))


def coreXml(title, ver, digest):
	return (
		'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
		'<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
		'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
		'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
		"<dc:title>%s — Manual de uso</dc:title><dc:subject>Manual de uso do complemento NotasWorkflowNVDA %s</dc:subject>"
		"<dc:creator>Wellington Cruz</dc:creator><dc:language>pt-BR</dc:language>"
		"<cp:keywords>NVDA; Notas Workflow NVDA; acessibilidade</cp:keywords>"
		"<dc:description>versao=%s; fonte-sha256=%s</dc:description><cp:version>%s</cp:version>"
		"</cp:coreProperties>" % (escape(title), escape(ver), escape(ver), digest, escape(ver))
	)


CONTENT_TYPES = (
	'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
	'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
	'<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
	'<Default Extension="xml" ContentType="application/xml"/>'
	'<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
	'<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
	'<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
	'<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
	'<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
	'<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
	'<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
	"</Types>"
)
ROOT_RELS = (
	'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
	'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
	'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
	'<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
	'<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
	"</Relationships>"
)
DOC_RELS = (
	'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
	'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
	'<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
	'<Relationship Id="rIdNumbering" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>'
	'<Relationship Id="rIdSettings" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>'
	'<Relationship Id="rIdFooter" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>'
	"</Relationships>"
)
SETTINGS = (
	'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
	'<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
	'<w:defaultTabStop w:val="709"/><w:characterSpacingControl w:val="doNotCompress"/>'
	'<w:themeFontLang w:val="pt-BR"/><w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat>'
	"</w:settings>"
)
APP = (
	'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
	'<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>NotasWorkflowNVDA gerar_manual.py</Application></Properties>'
)


def build(target=TARGET):
	with open(SOURCE, encoding="utf-8") as f:
		md = f.read()
	digest = sourceHash(md)
	ver = version()
	builder = Builder()
	parse(md.replace("{{versao}}", ver), builder)
	title = builder.headings[0][1]
	parts = {
		"[Content_Types].xml": CONTENT_TYPES,
		"_rels/.rels": ROOT_RELS,
		"docProps/core.xml": coreXml(title, ver, digest),
		"docProps/app.xml": APP,
		"word/document.xml": documentXml(builder, ver),
		"word/styles.xml": stylesXml(),
		"word/numbering.xml": numberingXml(builder.numbered),
		"word/settings.xml": SETTINGS,
		"word/footer1.xml": footerXml(ver),
		"word/_rels/document.xml.rels": DOC_RELS,
	}
	os.makedirs(os.path.dirname(target), exist_ok=True)
	tmp = target + ".tmp"
	with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
		for name, data in parts.items():
			info = zipfile.ZipInfo(name, ZIP_DATE)
			info.compress_type = zipfile.ZIP_DEFLATED
			z.writestr(info, data.encode("utf-8"))
	os.replace(tmp, target)
	print("manual: %s (%d seções, versão %s)" % (os.path.relpath(target, ROOT), len(builder.headings), ver))
	return target


def builtInfo(path=TARGET):
	"""(versão, sha256 da fonte) gravados no .docx, ou None."""
	try:
		with zipfile.ZipFile(path) as z:
			core = z.read("docProps/core.xml").decode("utf-8")
	except (OSError, KeyError, zipfile.BadZipFile):
		return None
	m = re.search(r"versao=([^;<]+); fonte-sha256=([0-9a-f]{64})", core)
	return (m.group(1), m.group(2)) if m else None


if __name__ == "__main__":
	build(sys.argv[1] if len(sys.argv) > 1 else TARGET)
