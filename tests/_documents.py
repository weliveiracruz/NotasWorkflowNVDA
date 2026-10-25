# -*- coding: UTF-8 -*-
"""Documents for the tests of "Note from document" and "Insert document" (FUN-33/34): small
but real Word (.docx), PowerPoint (.pptx), e-mail (.eml), HTML and text files, written with
the standard library only."""

import os
import zipfile
from email.message import EmailMessage
from xml.sax.saxutils import escape

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
A = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
P = 'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
R = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
RELS = "http://schemas.openxmlformats.org/package/2006/relationships"
NOTES = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide"
SLIDE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"


def _zip(path, parts):
	with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
		for name, text in parts.items():
			z.writestr(name, text if isinstance(text, bytes) else text.encode("utf-8"))
	return path


def _core(title):
	if title is None:
		return {}
	return {"docProps/core.xml": '<?xml version="1.0" encoding="UTF-8"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>%s</dc:title></cp:coreProperties>' % escape(title)}


# -- Word -----------------------------------------------------------------------------------------------

def run(text, bold=False, italic=False, strike=False):
	props = ("<w:b/>" if bold else "") + ("<w:i/>" if italic else "") + ("<w:strike/>" if strike else "")
	return '<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % ("<w:rPr>%s</w:rPr>" % props if props else "", escape(text))


def para(*runs, style=None, num=None, level=0):
	"""A paragraph; runs are run() strings or plain texts; num: id of a numbering (list)."""
	ppr = ""
	if style:
		ppr += '<w:pStyle w:val="%s"/>' % style
	if num:
		ppr += '<w:numPr><w:ilvl w:val="%d"/><w:numId w:val="%s"/></w:numPr>' % (level, num)
	body = "".join(r if r.startswith("<") else run(r) for r in runs)
	return "<w:p>%s%s</w:p>" % ("<w:pPr>%s</w:pPr>" % ppr if ppr else "", body)


def table(rows):
	cells = "".join("<w:tr>%s</w:tr>" % "".join("<w:tc>%s</w:tc>" % para(c) for c in row) for row in rows)
	return "<w:tbl>%s</w:tbl>" % cells


STYLES = (
	'<?xml version="1.0" encoding="UTF-8"?><w:styles %s>'
	'<w:style w:type="paragraph" w:styleId="Ttulo"><w:name w:val="Title"/></w:style>'
	'<w:style w:type="paragraph" w:styleId="Ttulo1"><w:name w:val="heading 1"/></w:style>'
	'<w:style w:type="paragraph" w:styleId="Ttulo2"><w:name w:val="heading 2"/></w:style>'
	'<w:style w:type="paragraph" w:styleId="Meu"><w:name w:val="Meu titulo"/><w:basedOn w:val="Ttulo2"/></w:style>'
	'<w:style w:type="paragraph" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
	"</w:styles>" % W
)
NUMBERING = (
	'<?xml version="1.0" encoding="UTF-8"?><w:numbering %s>'
	'<w:abstractNum w:abstractNumId="0"><w:lvl w:ilvl="0"><w:numFmt w:val="bullet"/></w:lvl></w:abstractNum>'
	'<w:abstractNum w:abstractNumId="1"><w:lvl w:ilvl="0"><w:numFmt w:val="decimal"/></w:lvl></w:abstractNum>'
	'<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num><w:num w:numId="2"><w:abstractNumId w:val="1"/></w:num>'
	"</w:numbering>" % W
)


def docx(path, body, title=None, extra=None):
	parts = {
		"[Content_Types].xml": '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
		"word/document.xml": '<?xml version="1.0" encoding="UTF-8"?><w:document %s><w:body>%s</w:body></w:document>' % (W, "".join(body)),
		"word/styles.xml": STYLES,
		"word/numbering.xml": NUMBERING,
	}
	parts.update(_core(title))
	parts.update(extra or {})
	return _zip(path, parts)


def sampleDocx(path):
	"""The Word document of the tests: every format the reader keeps."""
	return docx(path, [
		para("Relatório", style="Ttulo"),
		para("Resumo", style="Ttulo1"),
		para("Texto com ", run("negrito", bold=True), " e ", run("itálico", italic=True), " e ", run("riscado", strike=True), "."),
		para("Metas", style="Meu"),
		para("Primeiro", num="1"),
		para("Segundo", num="1"),
		para("Passo um", num="2"),
		para("Passo dois", num="2"),
		para(""),
		'<w:p><w:r><w:t>antes</w:t><w:tab/><w:t>depois</w:t><w:br/><w:t>linha nova</w:t></w:r><w:del><w:r><w:delText>apagado</w:delText></w:r></w:del></w:p>',
		table([["Mês", "Valor"], ["Janeiro", "10"]]),
	], title="Relatório trimestral")


# -- PowerPoint -------------------------------------------------------------------------------------------

def _shape(texts, ph=None, bullets=None):
	"""A shape with paragraphs; ph: placeholder type ("title", "body", "sldNum"...), "" for a body placeholder without type."""
	nvpr = "" if ph is None else ('<p:ph type="%s"/>' % ph if ph else '<p:ph idx="1"/>')
	paras = []
	for text in texts:
		ppr = ""
		if bullets == "none":
			ppr = "<a:pPr><a:buNone/></a:pPr>"
		elif bullets == "char":
			ppr = '<a:pPr><a:buChar char="•"/></a:pPr>'
		elif bullets == "num":
			ppr = '<a:pPr><a:buAutoNum type="arabicPeriod"/></a:pPr>'
		paras.append("<a:p>%s<a:r><a:t>%s</a:t></a:r></a:p>" % (ppr, escape(text)))
	return "<p:sp><p:nvSpPr><p:cNvPr id=\"1\" name=\"s\"/><p:cNvSpPr/><p:nvPr>%s</p:nvPr></p:nvSpPr><p:txBody>%s</p:txBody></p:sp>" % (nvpr, "".join(paras))


def _slide(shapes):
	return '<?xml version="1.0" encoding="UTF-8"?><p:sld %s %s %s><p:cSld><p:spTree>%s</p:spTree></p:cSld></p:sld>' % (P, A, R, "".join(shapes))


def pptx(path, slides, title=None):
	"""slides: [(shapes, notes texts or None)], in the order of the presentation. The files are
	numbered backwards (slide1.xml is the last one) to check that the order comes from the presentation."""
	count = len(slides)
	parts = {}
	ids = []
	rels = []
	for index, (shapes, notes) in enumerate(slides):
		fileNumber = count - index
		name = "slides/slide%d.xml" % fileNumber
		parts["ppt/" + name] = _slide(shapes)
		rels.append('<Relationship Id="rId%d" Type="%s" Target="%s"/>' % (index + 10, SLIDE, name))
		ids.append('<p:sldId id="%d" r:id="rId%d"/>' % (256 + index, index + 10))
		if notes:
			parts["ppt/notesSlides/notesSlide%d.xml" % fileNumber] = _slide([_shape(notes, ph="body"), _shape(["7"], ph="sldNum")]).replace("p:sld ", "p:notes ").replace("</p:sld>", "</p:notes>")
			parts["ppt/slides/_rels/slide%d.xml.rels" % fileNumber] = '<?xml version="1.0"?><Relationships xmlns="%s"><Relationship Id="rId1" Type="%s" Target="../notesSlides/notesSlide%d.xml"/></Relationships>' % (RELS, NOTES, fileNumber)
	parts["ppt/presentation.xml"] = '<?xml version="1.0" encoding="UTF-8"?><p:presentation %s %s><p:sldIdLst>%s</p:sldIdLst></p:presentation>' % (P, R, "".join(ids))
	parts["ppt/_rels/presentation.xml.rels"] = '<?xml version="1.0"?><Relationships xmlns="%s">%s</Relationships>' % (RELS, "".join(rels))
	parts.update(_core(title))
	return _zip(path, parts)


def samplePptx(path):
	table_ = (
		'<p:graphicFrame><a:graphic><a:graphicData><a:tbl><a:tr><a:tc><a:txBody><a:p><a:r><a:t>A</a:t></a:r></a:p></a:txBody></a:tc>'
		'<a:tc><a:txBody><a:p><a:r><a:t>B</a:t></a:r></a:p></a:txBody></a:tc></a:tr></a:tbl></a:graphicData></a:graphic></p:graphicFrame>'
	)
	return pptx(path, [
		([_shape(["Apresentação"], ph="ctrTitle"), _shape(["Subtítulo"], ph="subTitle"), _shape(["3"], ph="sldNum")], None),
		([_shape(["Agenda"], ph="title"), _shape(["Ponto A", "Ponto B"], ph=""), _shape(["Sem marcador"], ph="", bullets="none")], ["Falar devagar"]),
		([_shape(["Caixa de texto"]), _shape(["Um", "Dois"], bullets="num"), table_], None),
	])


# -- e-mail, HTML and text -------------------------------------------------------------------------------

def eml(path, html=True, attachment=True):
	msg = EmailMessage()
	msg["Subject"] = "Reunião de segunda"
	msg["From"] = "Ana <ana@example.com>"
	msg["To"] = "Bruno <bruno@example.com>"
	msg["Cc"] = "Carla <carla@example.com>"
	msg["Date"] = "Mon, 12 Oct 2026 14:30:00 -0300"
	msg.set_content("Olá,\nsegue a pauta.\n")
	if html:
		msg.add_alternative("<html><body><h2>Pauta</h2><ul><li><b>Orçamento</b></li><li>Prazos</li></ul><script>alert(1)</script></body></html>", subtype="html")
	if attachment:
		msg.add_attachment(b"%PDF-1.4", maintype="application", subtype="pdf", filename="pauta.pdf")
	with open(path, "wb") as f:
		f.write(bytes(msg))
	return path


def html(path, encoding="utf-8"):
	page = (
		'<html><head><meta charset="%s"><title>Página de teste</title><style>p{color:red}</style></head>'
		"<body><h1>Título</h1><p>Um <strong>texto</strong>  com   espaços.</p><script>alert(1)</script>"
		"<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table></body></html>"
	) % encoding
	with open(path, "wb") as f:
		f.write(page.encode(encoding))
	return path


def text(path, content, encoding="utf-8"):
	with open(path, "wb") as f:
		f.write(content.encode(encoding))
	return path


def folder():
	import tempfile

	return tempfile.mkdtemp(prefix="notasworkflownvda-docs-")


def path(folder_, name):
	return os.path.join(folder_, name)
