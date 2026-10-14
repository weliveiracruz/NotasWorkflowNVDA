# -*- coding: UTF-8 -*-
"""User manual tests (DOC-xx of docs/SDD-TESTES.md): the Word manual
(docs/Manual-NotasWorkflowNVDA.docx) exists, matches docs/manual/MANUAL.md and the
version, documents every control, lane, format and shortcut of the interface,
and is an accessible document.

Run:  python tests/test_manual.py   (after python build.py, which generates the .docx)"""

import ast
import os
import re
import sys
import zipfile
from xml.dom import minidom

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "docs", "manual"))

import build  # noqa: E402
import gerar_manual  # noqa: E402
from _results import Recorder  # noqa: E402

R = Recorder("manual (test_manual)")
PO = os.path.join(ROOT, "addon", "locale", "pt_BR", "LC_MESSAGES", "nvda.po")


def plain(label):
	"""What the manual calls a control: no &, no ':' at the end, no {placeholders}."""
	text = label.replace("&&", "\0").replace("&", "").replace("\0", "&")
	text = re.sub(r"\s*\(?\{\w+\}\)?", "", text)
	return text.rstrip(": ").strip()


def defaultGestures():
	"""NVDA+Alt+N... written as in the manual, from the scripts of the add-on."""
	with open(os.path.join(ROOT, "addon", "globalPlugins", "NotasWorkflowNVDA", "__init__.py"), encoding="utf-8") as f:
		tree = ast.parse(f.read())
	out = []
	for node in ast.walk(tree):
		if isinstance(node, ast.keyword) and node.arg == "gesture" and isinstance(node.value, ast.Constant):
			keys = node.value.value.split(":", 1)[1].split("+")
			out.append("+".join(k.upper() if k.lower() == "nvda" else k.capitalize() for k in keys))
	return out


def run():
	man = build.readManifest()
	version = man["version"]
	path = gerar_manual.TARGET
	with open(gerar_manual.SOURCE, encoding="utf-8") as f:
		md = f.read()

	# -- DOC-01 the Word file ---------------------------------------------------------------------
	R.check("DOC-01 the Word manual exists in the documentation folder", os.path.isfile(path) and os.path.dirname(path) == os.path.join(ROOT, "docs"), path)
	try:
		z = zipfile.ZipFile(path)
		parts = {n: z.read(n).decode("utf-8") for n in z.namelist()}
		for xml in parts.values():
			minidom.parseString(xml.encode("utf-8"))
		valid = {"[Content_Types].xml", "word/document.xml", "word/styles.xml", "docProps/core.xml"} <= set(parts)
	except Exception as e:
		parts, valid = {}, False
		R.check("DOC-01 the Word manual opens", False, repr(e))
	R.check("DOC-01 the Word manual is a valid .docx (every part is well-formed XML)", valid)

	# -- DOC-02 up to date --------------------------------------------------------------------------
	info = gerar_manual.builtInfo(path)
	R.check("DOC-02 the .docx was generated from the current MANUAL.md (run python build.py)", info is not None and info[1] == gerar_manual.sourceHash(md), info)
	R.check("DOC-02 the .docx is of the current version %s" % version, info is not None and info[0] == version, info)
	R.check("DOC-02 the manual history has a row for version %s" % version, re.search(r"^\|\s*%s\s*\|" % re.escape(version), md, re.M) is not None)
	document = parts.get("word/document.xml", "")
	R.check("DOC-02 the cover shows the version", "versão %s" % version in document)

	# -- DOC-03 every control of the interface is documented ------------------------------------------
	po = build.parsePo(PO)
	po.pop("", None)
	labels = sorted({plain(v) for k, v in po.items() if re.search(r"&[^&\s]", k)})
	missing = [lbl for lbl in labels if lbl and lbl not in md]
	R.check("DOC-03 every button, field and menu of the interface is in the manual (%d)" % len(labels), not missing, missing)
	lanes = [po[k] for k in ("To do", "In progress", "Blocked", "Done")]
	R.check("DOC-03 the four lanes are explained", all(lane in md for lane in lanes), lanes)
	formats = [po[k] for k in ("Bold", "Italic", "Strikethrough", "Inline code", "Heading 2", "Heading 3", "Bulleted list", "Numbered list", "Quote", "Divider")]
	R.check("DOC-03 every format of the Formatting menu is explained", all(f in md for f in formats), [f for f in formats if f not in md])
	options = [po[k] for k in ("All notes", "Loose notes", "Recent notes", "Lanes (tree)", "Table", "Saved", "Unsaved changes…", "Not saved", "Without folder")]
	R.check("DOC-03 every option of Show, View and Save status is explained", all(o in md for o in options), [o for o in options if o not in md])
	columns = [po[k] for k in ("Title", "Status", "Notebook", "Tags", "Updated on", "Excerpt", "Relevance")]
	R.check("DOC-03 every column of the tables is explained", all(c in md for c in columns), [c for c in columns if c not in md])

	# -- DOC-04 shortcuts ------------------------------------------------------------------------------------
	gestures = defaultGestures()
	R.check("DOC-04 every default shortcut is in the manual", gestures and all(g in md for g in gestures), (gestures, [g for g in gestures if g not in md]))
	keys = ("Alt+Shift+Seta para a direita", "Alt+Shift+Seta para a esquerda", "Ctrl+S", "Ctrl+B", "Ctrl+I", "F2", "Delete", "Esc", "Enter")
	R.check("DOC-04 the keys inside the windows are in the manual", all(k in md for k in keys), [k for k in keys if k not in md])

	# -- DOC-05 accessible document ---------------------------------------------------------------------------------
	styles = parts.get("word/styles.xml", "")
	core = parts.get("docProps/core.xml", "")
	R.check("DOC-05 headings use Word heading styles (navigable with a screen reader)", document.count('w:pStyle w:val="Heading1"') >= 10 and 'w:outlineLvl w:val="0"' in styles)
	R.check("DOC-05 every table has a header row repeated on each page", document.count("<w:tbl>") == document.count("<w:tblHeader/>") and document.count("<w:tbl>") >= 10)
	R.check("DOC-05 language pt-BR and title in the properties", 'w:lang w:val="pt-BR"' in styles and "<dc:language>pt-BR</dc:language>" in core and "<dc:title>" in core)
	links = re.findall(r'w:hyperlink w:anchor="(\w+)"', document)
	marks = set(re.findall(r'w:bookmarkStart w:id="\d+" w:name="(\w+)"', document))
	R.check("DOC-05 the table of contents links to every chapter", links and all(a in marks for a in links), len(links))
	R.check("DOC-05 no image without description (the manual has no images)", "<w:drawing" not in document and "<pic:" not in document)


if __name__ == "__main__":
	try:
		run()
	except Exception:
		import traceback

		traceback.print_exc()
		R.check("suite finished without crashing", False, traceback.format_exc()[-800:])
	sys.exit(R.finish())
