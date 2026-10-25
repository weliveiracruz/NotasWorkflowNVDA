# -*- coding: UTF-8 -*-
"""User manual tests (DOC-xx of docs/SDD-TESTES.md): the HTML manual shown by the
User manual button (addon/doc/pt_BR/manual.html) exists, goes into the package,
matches docs/manual/MANUAL.md and the version, documents every control, lane,
format and shortcut of the interface, and is an accessible document.

Run:  python tests/test_manual.py   (after python build.py, which generates manual.html)"""

import ast
import os
import re
import sys
import zipfile
from html.parser import HTMLParser

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


class Structure(HTMLParser):
	"""Tags, ids, links and open elements of the page (for well-formedness and structure)."""

	VOID = {"meta", "br", "hr", "img", "link", "input"}

	def __init__(self):
		super().__init__()
		self.tags = []
		self.ids = set()
		self.links = []
		self.stack = []
		self.errors = []
		self.attrs = []

	def handle_starttag(self, tag, attrs):
		attrs = dict(attrs)
		self.tags.append(tag)
		self.attrs.append((tag, attrs))
		if "id" in attrs:
			self.ids.add(attrs["id"])
		if tag == "a" and "href" in attrs:
			self.links.append(attrs["href"])
		if tag not in self.VOID:
			self.stack.append(tag)

	def handle_endtag(self, tag):
		if not self.stack or self.stack[-1] != tag:
			self.errors.append(tag)
		else:
			self.stack.pop()


def run():
	man = build.readManifest()
	version = man["version"]
	path = gerar_manual.TARGET
	with open(gerar_manual.SOURCE, encoding="utf-8") as f:
		md = f.read()

	# -- DOC-01 the HTML file, inside the package ------------------------------------------------------
	R.check("DOC-01 the manual is in the add-on (addon/doc/pt_BR/manual.html)", os.path.isfile(path) and path == os.path.join(ROOT, "addon", "doc", "pt_BR", "manual.html"), path)
	try:
		with open(path, encoding="utf-8") as f:
			page = f.read()
	except OSError as e:
		page = ""
		R.check("DOC-01 the manual opens", False, repr(e))
	parser = Structure()
	parser.feed(page)
	R.check("DOC-01 the manual is well-formed HTML (every element closed in order)", page and not parser.errors and not parser.stack, (parser.errors[:5], parser.stack[:5]))
	package = os.path.join(build.DIST, "%s-%s.nvda-addon" % (man["name"], man["version"]))
	try:
		with zipfile.ZipFile(package) as z:
			packed = z.read("doc/pt_BR/manual.html").decode("utf-8")
	except (OSError, KeyError, zipfile.BadZipFile):
		packed = None
	R.check("DOC-01 the package of the version has the same manual", packed == page, package)
	R.check("DOC-01 no Word manual is generated any more", not os.path.exists(os.path.join(ROOT, "docs", "Manual-NotasWorkflowNVDA.docx")))

	# -- DOC-02 up to date --------------------------------------------------------------------------
	info = gerar_manual.builtInfo(path)
	R.check("DOC-02 the manual was generated from the current MANUAL.md (run python build.py)", info is not None and info[1] == gerar_manual.sourceHash(md), info)
	R.check("DOC-02 the manual is of the current version %s" % version, info is not None and info[0] == version, info)
	R.check("DOC-02 the manual history has a row for version %s" % version, re.search(r"^\|\s*%s\s*\|" % re.escape(version), md, re.M) is not None)
	R.check("DOC-02 the top of the manual shows the version", "versão %s" % version in page)

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
	options = [plain(po[k]) for k in ("All notes", "Loose notes", "Recent notes", "Saved", "Unsaved changes…", "Not saved", "Without folder", "Loose note (no notebook or folder)", "&Note…", "Note&book…", "&Folder…")]
	R.check("DOC-03 every option of Show, Create, Location and Save status is explained", all(o in md for o in options), [o for o in options if o not in md])
	columns = [po[k] for k in ("Title", "Updated on", "Excerpt", "Relevance")]
	R.check("DOC-03 every column of the search results is explained", all(c in md for c in columns), [c for c in columns if c not in md])

	# -- DOC-04 shortcuts ------------------------------------------------------------------------------------
	gestures = defaultGestures()
	R.check("DOC-04 every default shortcut is in the manual", gestures and all(g in md for g in gestures), (gestures, [g for g in gestures if g not in md]))
	keys = ("Alt+Shift+Seta para a direita", "Alt+Shift+Seta para a esquerda", "Ctrl+S", "Ctrl+B", "Ctrl+I", "F2", "Delete", "Esc", "Enter")
	R.check("DOC-04 the keys inside the windows are in the manual", all(k in md for k in keys), [k for k in keys if k not in md])

	# -- DOC-05 accessible document ---------------------------------------------------------------------------------
	tags = parser.tags
	R.check("DOC-05 language pt-BR and a title", '<html lang="pt-BR">' in page and '<main lang="pt-BR">' in page and re.search(r"<title>[^<]+</title>", page) is not None)
	R.check("DOC-05 one h1, chapters in h2 and sections in h3 (navigable with H, 1, 2 and 3)", tags.count("h1") == 1 and tags.count("h2") >= 10 and tags.count("h3") >= 10 and "h4" not in tags, (tags.count("h1"), tags.count("h2"), tags.count("h3")))
	tables = tags.count("table")
	heads = [a for t, a in parser.attrs if t == "th"]
	R.check("DOC-05 every table has a header row (th scope=col)", tables >= 10 and tags.count("thead") == tables and heads and all(a.get("scope") == "col" for a in heads), tables)
	R.check("DOC-05 the table of contents links to every chapter", parser.links and all(h.startswith("#") and h[1:] in parser.ids for h in parser.links) and len(parser.links) == tags.count("h2") - 1, len(parser.links))
	R.check("DOC-05 no script, frame, form, external file or image", not {"script", "iframe", "form", "img", "link", "object"} & set(tags) and "http" not in page.lower())

	# -- DOC-06 only this add-on ------------------------------------------------------------------------------------
	userTexts = {"docs/manual/MANUAL.md": md}
	for rel in ("readme.md", "docs/pt_BR/readme.md", "addon/manifest.ini", "addon/locale/pt_BR/manifest.ini"):
		with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
			userTexts[rel] = f.read()
	userTexts["translations"] = "\n".join(po.values())
	pattern = re.compile(r"\bweb\b|aplica[cç][aã]o web|TipTap|localStorage", re.I)
	found = ["%s: %s" % (name, m.group(0)) for name, text in userTexts.items() for m in pattern.finditer(text)]
	R.check("DOC-06 the user texts do not mention another platform (manual, readmes, manifests, interface)", not found, found[:5])


if __name__ == "__main__":
	try:
		run()
	except Exception:
		import traceback

		traceback.print_exc()
		R.check("suite finished without crashing", False, traceback.format_exc()[-800:])
	sys.exit(R.finish())
