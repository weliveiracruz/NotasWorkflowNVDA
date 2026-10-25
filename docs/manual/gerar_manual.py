# -*- coding: UTF-8 -*-
"""Gera o manual de uso em HTML (addon/doc/pt_BR/manual.html) a partir de
docs/manual/MANUAL.md. Só biblioteca padrão do Python, como o resto do projeto.
O manual vai dentro do pacote: o botão Manual de uso… da janela principal o mostra
na janela de navegação do NVDA.

Uso:  python docs/manual/gerar_manual.py   (o build.py também roda este script)

Markdown aceito: # título, ## capítulos, ### seções, parágrafos, listas "- " e "1. ", tabelas,
citações "> " (caixa de destaque), **negrito**, `código` e ``código com `crase` ``.
{{versao}} vira a versão de addon/manifest.ini.

O documento é acessível: idioma pt-BR, título, um só h1, capítulos em h2 e seções em h3
(navegáveis com H, 1, 2 e 3 no NVDA), sumário com links, tabelas com cabeçalho (th scope="col")
e nenhum script, estilo externo ou imagem. A versão e o SHA-256 do MANUAL.md ficam num meta
para os testes saberem se o HTML está atualizado."""

import hashlib
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SOURCE = os.path.join(HERE, "MANUAL.md")
TARGET = os.path.join(ROOT, "addon", "doc", "pt_BR", "manual.html")


def version():
	with open(os.path.join(ROOT, "addon", "manifest.ini"), encoding="utf-8") as f:
		return re.search(r"^version\s*=\s*(\S+)", f.read(), re.M).group(1)


def sourceHash(text):
	return hashlib.sha256(text.encode("utf-8")).hexdigest()


# -- inline -----------------------------------------------------------------------------------

_INLINE = re.compile(r"(``(.+?)``|`([^`]+)`|\*\*(.+?)\*\*)")


def inline(text):
	"""HTML of a line with **bold** and `code` (everything else escaped)."""
	out = []
	pos = 0
	for m in _INLINE.finditer(text):
		out.append(html.escape(text[pos:m.start()], quote=False))
		if m.group(4) is not None:
			out.append("<strong>%s</strong>" % html.escape(m.group(4), quote=False))
		else:
			code = m.group(2).strip() if m.group(2) is not None else m.group(3)
			out.append("<code>%s</code>" % html.escape(code, quote=False))
		pos = m.end()
	out.append(html.escape(text[pos:], quote=False))
	return "".join(out)


# -- blocks ----------------------------------------------------------------------------------------


class Builder:
	def __init__(self):
		self.body = []
		self.headings = []  # (level, text, anchor)

	def heading(self, level, text):
		anchor = "secao%d" % (len(self.headings) + 1)
		self.headings.append((level, text, anchor))
		self.body.append('<h%d id="%s">%s</h%d>' % (level, anchor, inline(text), level))

	def text(self, line):
		self.body.append("<p>%s</p>" % inline(line))

	def bullets(self, items):
		self.body.append("<ul>\n%s\n</ul>" % "\n".join("<li>%s</li>" % inline(i) for i in items))

	def ordered(self, items):
		self.body.append("<ol>\n%s\n</ol>" % "\n".join("<li>%s</li>" % inline(i) for i in items))

	def note(self, line):
		self.body.append('<aside class="destaque"><p>%s</p></aside>' % inline(line))

	def table(self, rows):
		cols = max(len(r) for r in rows)
		rows = [r + [""] * (cols - len(r)) for r in rows]
		xml = ["<table>", "<thead><tr>%s</tr></thead>" % "".join('<th scope="col">%s</th>' % inline(c) for c in rows[0]), "<tbody>"]
		for row in rows[1:]:
			xml.append("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in row))
		xml.append("</tbody>\n</table>")
		self.body.append("\n".join(xml))


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


# -- page ------------------------------------------------------------------------------------

STYLE = """body{font-family:Segoe UI,Calibri,sans-serif;line-height:1.5;max-width:60em;margin:1em auto;padding:0 1em}
h1,h2,h3{color:#1F4E79}h2{border-bottom:2px solid #1F4E79;padding-bottom:.2em;margin-top:2em}
table{border-collapse:collapse;margin:1em 0}th,td{border:1px solid #A6A6A6;padding:.3em .6em;text-align:left;vertical-align:top}
th{background:#DCE6F1}code{font-family:Consolas,monospace;background:#F2F2F2;padding:0 .2em}
aside.destaque{border-left:6px solid #1F4E79;background:#EAF1F8;padding:.2em 1em;margin:1em 0}"""


def page(md, ver):
	builder = Builder()
	parse(md.replace("{{versao}}", ver), builder)
	title = builder.headings[0][1] if builder.headings and builder.headings[0][0] == 1 else "Manual"
	toc = "\n".join('<li><a href="#%s">%s</a></li>' % (a, inline(t)) for level, t, a in builder.headings if level == 2)
	# The first heading (the title) goes before the table of contents.
	body = [builder.body[0], "<p>Manual de uso — versão %s</p>" % html.escape(ver), '<nav aria-label="Sumário">\n<h2>Sumário</h2>\n<ul>\n%s\n</ul>\n</nav>' % toc] + builder.body[1:]
	return (
		'<!DOCTYPE html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
		'<meta name="manual" content="versao=%s; fonte-sha256=%s">\n'
		'<title>%s — Manual de uso</title>\n<style>\n%s\n</style>\n</head>\n<body>\n<main lang="pt-BR">\n%s\n</main>\n</body>\n</html>\n'
	) % (html.escape(ver), sourceHash(md), html.escape(title), STYLE, "\n".join(body)), builder


def build(target=TARGET):
	with open(SOURCE, encoding="utf-8") as f:
		md = f.read()
	ver = version()
	text, builder = page(md, ver)
	os.makedirs(os.path.dirname(target), exist_ok=True)
	tmp = target + ".tmp"
	with open(tmp, "w", encoding="utf-8", newline="\n") as f:
		f.write(text)
	os.replace(tmp, target)
	print("manual: %s (%d seções, versão %s)" % (os.path.relpath(target, ROOT), len(builder.headings), ver))
	return target


def builtInfo(path=TARGET):
	"""(versão, sha256 da fonte) gravados no HTML, ou None."""
	try:
		with open(path, encoding="utf-8") as f:
			head = f.read(2000)
	except OSError:
		return None
	m = re.search(r'<meta name="manual" content="versao=([^;"]+); fonte-sha256=([0-9a-f]{64})">', head)
	return (m.group(1), m.group(2)) if m else None


if __name__ == "__main__":
	build(sys.argv[1] if len(sys.argv) > 1 else TARGET)
