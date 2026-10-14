# -*- coding: UTF-8 -*-
"""Builds the NotasWorkflowNVDA add-on package (dist/NotasWorkflowNVDA-<version>.nvda-addon).

Usage:
  python build.py             builds the package (used by the test suite)
  python build.py --release   runs EVERY test suite first (tests/run_all.py) and
                              refuses to build when any test fails (docs/SDD.md, section 8)

Only the Python standard library is needed. The script:
  1. checks manifest.ini;
  2. compiles the translations (locale/*/LC_MESSAGES/nvda.po -> nvda.mo);
  3. converts the documentation (readme.md, docs/pt_BR/readme.md) to addon/doc/<lang>/readme.html
     and generates the Word user manual (docs/manual/MANUAL.md -> docs/Manual-NotasWorkflowNVDA.docx);
  4. zips the addon folder and prints the SHA-256 (needed by the Add-on Store).
"""

import ast
import hashlib
import html
import os
import re
import struct
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.join(ROOT, "addon")
DIST = os.path.join(ROOT, "dist")

DOCS = {
	"en": os.path.join(ROOT, "readme.md"),
	"pt_BR": os.path.join(ROOT, "docs", "pt_BR", "readme.md"),
}


def readManifest(path=None):
	path = path or os.path.join(ADDON, "manifest.ini")
	data = {}
	with open(path, encoding="utf-8") as f:
		text = f.read()
	for m in re.finditer(r'^(\w+)\s*=\s*("""(.*?)"""|"(.*?)"|(.*?))\s*$', text, re.M | re.S):
		value = m.group(3) if m.group(3) is not None else (m.group(4) if m.group(4) is not None else m.group(5))
		data[m.group(1)] = value
	return data


def checkManifest(man):
	required = ("name", "summary", "description", "author", "url", "version", "minimumNVDAVersion", "lastTestedNVDAVersion", "docFileName", "changelog")
	missing = [k for k in required if not man.get(k)]
	if missing:
		sys.exit("manifest.ini: missing %s" % ", ".join(missing))
	if not re.fullmatch(r"\d+\.\d+\.\d+", man["version"]):
		sys.exit("manifest.ini: version must be major.minor.patch")
	for key in ("minimumNVDAVersion", "lastTestedNVDAVersion"):
		if not re.fullmatch(r"\d{4}\.\d+(\.\d+)?", man[key]):
			sys.exit("manifest.ini: invalid %s" % key)
	if tuple(map(int, man["minimumNVDAVersion"].split("."))) > tuple(map(int, man["lastTestedNVDAVersion"].split("."))):
		sys.exit("manifest.ini: minimumNVDAVersion is newer than lastTestedNVDAVersion")
	if not man["url"].startswith("https://"):
		sys.exit("manifest.ini: url must start with https://")


# --- msgfmt (compile .po to .mo) --------------------------------------------------

def parsePo(path):
	messages = {}
	msgid = msgstr = None
	section = None
	fuzzy = False

	def flush():
		if msgid is not None and msgstr is not None and not fuzzy and (msgstr or msgid == ""):
			messages[msgid] = msgstr

	with open(path, encoding="utf-8") as f:
		for line in f:
			line = line.strip()
			if line.startswith("#,") and "fuzzy" in line:
				fuzzy = True
			elif line.startswith("msgid "):
				flush()
				msgid, msgstr, section = ast.literal_eval(line[6:]), None, "id"
			elif line.startswith("msgstr "):
				msgstr, section = ast.literal_eval(line[7:]), "str"
			elif line.startswith('"'):
				if section == "id":
					msgid += ast.literal_eval(line)
				elif section == "str":
					msgstr += ast.literal_eval(line)
			elif not line:
				flush()
				msgid = msgstr = section = None
				fuzzy = False
	flush()
	return messages


def writeMo(messages, path):
	keys = sorted(messages)
	ids = b""
	strs = b""
	offsets = []
	for k in keys:
		kb = k.encode("utf-8")
		vb = messages[k].encode("utf-8")
		offsets.append((len(ids), len(kb), len(strs), len(vb)))
		ids += kb + b"\0"
		strs += vb + b"\0"
	n = len(keys)
	keyStart = 7 * 4 + 16 * n
	valueStart = keyStart + len(ids)
	koffsets = []
	voffsets = []
	for o1, l1, o2, l2 in offsets:
		koffsets += [l1, o1 + keyStart]
		voffsets += [l2, o2 + valueStart]
	output = struct.pack("Iiiiiii", 0x950412DE, 0, n, 7 * 4, 7 * 4 + n * 8, 0, 0)
	output += struct.pack("%di" % len(koffsets), *koffsets)
	output += struct.pack("%di" % len(voffsets), *voffsets)
	output += ids + strs
	with open(path, "wb") as f:
		f.write(output)


def compileTranslations():
	localeDir = os.path.join(ADDON, "locale")
	for lang in sorted(os.listdir(localeDir)):
		po = os.path.join(localeDir, lang, "LC_MESSAGES", "nvda.po")
		if os.path.isfile(po):
			messages = parsePo(po)
			writeMo(messages, po[:-3] + ".mo")
			print("translation %s: %d messages" % (lang, len(messages) - 1))


# --- documentation (small Markdown subset -> HTML) --------------------------------------

def _inline(text):
	text = html.escape(text, quote=False)
	text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
	text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
	text = re.sub(r"\[([^\]]+)\]\((https://[^)\s]+)\)", r'<a href="\2">\1</a>', text)
	return text


def markdownToHtml(md):
	out = []
	lines = md.splitlines()
	i = 0
	while i < len(lines):
		line = lines[i]
		if not line.strip():
			i += 1
			continue
		m = re.match(r"^(#{1,6})\s+(.*)$", line)
		if m:
			level = len(m.group(1))
			out.append("<h%d>%s</h%d>" % (level, _inline(m.group(2)), level))
			i += 1
			continue
		if line.startswith("|"):
			rows = []
			while i < len(lines) and lines[i].startswith("|"):
				cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
				if not all(re.fullmatch(r":?-+:?", c) for c in cells):
					rows.append(cells)
				i += 1
			out.append("<table>")
			for n, row in enumerate(rows):
				tag = "th" if n == 0 else "td"
				out.append("<tr>%s</tr>" % "".join("<%s>%s</%s>" % (tag, _inline(c), tag) for c in row))
			out.append("</table>")
			continue
		if re.match(r"^\s*([*-]|\d+\.)\s+", line):
			ordered = bool(re.match(r"^\s*\d+\.", line))
			tag = "ol" if ordered else "ul"
			out.append("<%s>" % tag)
			while i < len(lines) and re.match(r"^\s*([*-]|\d+\.)\s+", lines[i]):
				out.append("<li>%s</li>" % _inline(re.sub(r"^\s*([*-]|\d+\.)\s+", "", lines[i])))
				i += 1
			out.append("</%s>" % tag)
			continue
		para = []
		while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||\s*([*-]|\d+\.)\s)", lines[i]):
			para.append(lines[i].strip())
			i += 1
		out.append("<p>%s</p>" % _inline(" ".join(para)))
	return "\n".join(out)


def buildDocs(man):
	for lang, source in DOCS.items():
		with open(source, encoding="utf-8") as f:
			md = f.read()
		title = md.splitlines()[0].lstrip("# ").strip()
		page = (
			'<!DOCTYPE html>\n<html lang="%s">\n<head>\n<meta charset="utf-8">\n'
			"<title>%s</title>\n</head>\n<body>\n<main>\n%s\n</main>\n</body>\n</html>\n"
		) % (lang.replace("_", "-"), html.escape(title), markdownToHtml(md))
		outDir = os.path.join(ADDON, "doc", lang)
		os.makedirs(outDir, exist_ok=True)
		with open(os.path.join(outDir, man["docFileName"]), "w", encoding="utf-8") as f:
			f.write(page)
		print("doc %s: %s" % (lang, os.path.relpath(os.path.join(outDir, man["docFileName"]), ROOT)))


# --- package ------------------------------------------------------------------------

def buildPackage(man):
	os.makedirs(DIST, exist_ok=True)
	target = os.path.join(DIST, "%s-%s.nvda-addon" % (man["name"], man["version"]))
	with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
		for folder, dirs, files in os.walk(ADDON):
			dirs[:] = sorted(d for d in dirs if d != "__pycache__")
			for name in sorted(files):
				if name.endswith((".pyc", ".pyo", ".po", ".pot")):
					continue
				full = os.path.join(folder, name)
				z.write(full, os.path.relpath(full, ADDON).replace(os.sep, "/"))
	with open(target, "rb") as f:
		digest = hashlib.sha256(f.read()).hexdigest()
	with open(target + ".sha256", "w") as f:
		f.write("%s  %s\n" % (digest, os.path.basename(target)))
	print("\npackage: %s" % os.path.relpath(target, ROOT))
	print("SHA-256: %s" % digest)
	return target


def buildManual():
	"""Word user manual, regenerated at every build so it never lags behind MANUAL.md."""
	sys.path.insert(0, os.path.join(ROOT, "docs", "manual"))
	import gerar_manual

	gerar_manual.build()


def runAllTests():
	"""Release gate: every suite of docs/SDD-TESTES.md must pass (0 failures)."""
	print("Running every test suite before building the release...\n")
	cmd = [sys.executable, os.path.join(ROOT, "tests", "run_all.py"), "--note", "build.py --release"]
	proc = subprocess.run(cmd, cwd=ROOT)  # nosec B603 - fixed command, no shell
	if proc.returncode != 0:
		sys.exit("\nRELEASE REFUSED: at least one test failed. Fix it, run the tests again and build afterwards.")


if __name__ == "__main__":
	manifest = readManifest()
	checkManifest(manifest)
	if "--release" in sys.argv:
		runAllTests()
	compileTranslations()
	buildDocs(manifest)
	buildManual()
	buildPackage(manifest)
