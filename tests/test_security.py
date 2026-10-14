# -*- coding: UTF-8 -*-
"""Vulnerability and privacy tests (SEG-xx of docs/SDD-TESTES.md): no network,
no note content in the log, hostile files and HTML, size limits, atomic writes,
confirmations, secure screens, static analysis.

Run:  python tests/test_security.py   (bandit must be installed: pip install bandit)"""

import ast
import builtins
import json
import os
import re
import socket
import subprocess  # nosec B404 - runs bandit in the test only
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from _guiapp import RECORD, NotasWorkflowNVDA, markup, newPlugin, pump, store, wx  # noqa: E402
import _helpers  # noqa: E402
import nvda_stubs  # noqa: E402
from _results import Recorder  # noqa: E402

R = Recorder("security (test_security)")
ADDON = os.path.join(_helpers.ROOT, "addon")
SECRET = "SEGREDO-da-folha-7f3a"


def addonSources():
	out = {}
	for folder, dirs, files in os.walk(ADDON):
		dirs[:] = [d for d in dirs if d != "__pycache__"]
		for f in files:
			if f.endswith(".py"):
				p = os.path.join(folder, f)
				with open(p, encoding="utf-8") as fh:
					out[os.path.relpath(p, _helpers.ROOT)] = fh.read()
	return out


def imports(sources):
	found = set()
	for s in sources.values():
		for node in ast.walk(ast.parse(s)):
			if isinstance(node, ast.Import):
				found.update(a.name.split(".")[0] for a in node.names)
			elif isinstance(node, ast.ImportFrom) and node.level == 0:
				found.add(node.module.split(".")[0])
	return found


def writeFile(content, binary=False):
	path = os.path.join(_helpers.tempFolder(), "file.json")
	with open(path, "wb" if binary else "w", **({} if binary else {"encoding": "utf-8"})) as fh:
		fh.write(content)
	return path


def run():
	sources = addonSources()
	imported = imports(sources)

	# -- SEG-01 no network ----------------------------------------------------------------------
	network = {"socket", "ssl", "urllib", "http", "ftplib", "smtplib", "telnetlib", "xmlrpc", "asyncio", "requests", "websocket", "poplib", "imaplib"}
	R.check("SEG-01 the add-on imports no network module", not (imported & network), sorted(imported & network))
	R.check("SEG-01 no web address in the code (nothing is sent anywhere)", not any(re.search(r"https?://", s) for p, s in sources.items()), [p for p, s in sources.items() if re.search(r"https?://", s)])
	attempts = []
	original = socket.socket

	class NoNetwork(original):
		def __init__(self, *a, **k):
			attempts.append(a)
			raise OSError("network blocked by the test")

	socket.socket = NoNetwork
	try:
		plugin = newPlugin()
		note = plugin.store.addNote("Folha secreta " + SECRET)
		plugin.store.updateNote(note["id"], content=markup.textToHtml("conteúdo " + SECRET), tags=[SECRET])
		from NotasWorkflowNVDA import search

		search.search(plugin.store.notes, SECRET)
		plugin.openWindow()
		plugin.script_lanesSummary(None)
		exported = os.path.join(_helpers.tempFolder(), "e.json")
		plugin.exportNotes(exported)
		plugin.importNotes(exported)
	finally:
		socket.socket = original
	R.check("SEG-01 using the add-on opens no connection", not attempts, attempts)

	# -- SEG-02 note content never in the log -------------------------------------------------------
	folder = plugin.store.folder
	# Earlier changes written first: the impossible folder below must only get this change.
	plugin.store.flush()
	plugin.store.folder = os.path.join(plugin.store.path, "impossible")
	plugin.safe(plugin.store.updateNote, note["id"], title="outro " + SECRET)
	# The write runs in the background: wait for it (it fails) before restoring the folder.
	plugin.store.flush()
	pump(timeout=0.3)
	plugin.store.folder = folder
	plugin.store.flush()
	with open(plugin.store.path, "w", encoding="utf-8") as fh:
		fh.write('{"notes": [{"id": "x", "title": "' + SECRET + '"')
	broken = newPlugin(folder)
	bad = writeFile("{" + SECRET)
	broken.importNotes(bad)
	logs = RECORD["log"]
	R.check("SEG-02 note titles, contents and tags never reach the NVDA log", not any(SECRET in x for x in logs), [x for x in logs if SECRET in x][:2])
	R.check("SEG-02 errors are logged only by kind", any("NotasWorkflowNVDA: write" in x for x in logs) and any("damaged data file" in x for x in logs), logs[-5:])
	try:
		raise store.StoreError("write", "y" * 10000)
	except store.StoreError as e:
		R.check("SEG-02 error detail limited to 200 characters", len(e.detail) == 200)

	# -- SEG-03 dangerous functions and dependencies ---------------------------------------------------
	pattern = re.compile(r"(?<![\w.])(eval|exec|compile)\s*\(|\bpickle\b|\bmarshal\b|\bshelve\b|\bsubprocess\b|os\.system|os\.popen|os\.startfile|shell\s*=\s*True|__import__|yaml\.load|ctypes")
	bad = ["%s: %s" % (p, m.group(0)) for p, s in sources.items() for m in pattern.finditer(s)]
	R.check("SEG-03 no eval, exec, pickle, subprocess, shell or ctypes in the add-on", not bad, bad)
	allowed = {"datetime", "heapq", "html", "json", "os", "re", "shutil", "threading", "time", "uuid", "unicodedata",
		"addonHandler", "config", "globalPluginHandler", "globalVars", "gui", "queueHandler", "ui", "wx", "logHandler", "scriptHandler"}
	R.check("SEG-03 only the standard library and NVDA (no third-party dependency)", imported <= allowed, sorted(imported - allowed))

	# -- SEG-04 size limits ------------------------------------------------------------------------------
	big = os.path.join(_helpers.tempFolder(), "big.json")
	with open(big, "wb") as fh:
		fh.seek(store.MAX_FILE_SIZE + 10)
		fh.write(b"]")
	reads = []
	realOpen = builtins.open

	def watchOpen(path, *a, **k):
		if str(path) == big:
			reads.append(path)
		return realOpen(path, *a, **k)

	s = _helpers.newStore(_helpers.loadCore())
	builtins.open = watchOpen
	try:
		try:
			s.importFile(big)
			R.check("SEG-04 import above 20 MB refused", False, "accepted")
		except store.StoreError as e:
			R.check("SEG-04 import above 20 MB refused without reading it", e.kind == "tooLarge" and not reads, (e.kind, len(reads)))
	finally:
		builtins.open = realOpen
	dataFolder = _helpers.tempFolder()
	os.replace(big, os.path.join(dataFolder, store.FILE_NAME))
	s = store.NotesStore(dataFolder)
	s.load()
	R.check("SEG-04 data file above 20 MB is not loaded (kept aside, never deleted)", s.notes == [] and s.warning and s.warning[0] == "corrupt" and any(".corrupt-" in f for f in os.listdir(dataFolder)))

	# -- SEG-05 validation of untrusted data ----------------------------------------------------------------
	from NotasWorkflowNVDA import model

	refused = [v for v in ("../x", "a/b", "a\\b", "", "a" * 65, "x y", "é", None, 5, "a?b") if model.isValidId(v)]
	R.check("SEG-05 ids with path or odd characters are refused", not refused, refused)
	hostile = {
		"folders": [{"id": "f1", "name": "<b>x</b>" + "n" * 500, "color": "red;background:url(x)"}],
		"notebooks": [{"id": "n1", "name": "nb", "folderId": "../../f1"}, {"id": "n2", "name": "", "folderId": "f1"}],
		"notes": [
			{"id": "a", "title": "t" * 5000, "content": "c" * (model.MAX_CONTENT + 1), "tags": ["x"] * 500 + [{"o": 1}], "laneId": "<script>", "notebookId": "n1", "createdAt": "2026-13-45", "__proto__": {"admin": True}},
			{"id": "b", "title": ["list"], "content": {"x": 1}, "tags": None, "notebookId": "n2"},
		],
	}
	s = _helpers.newStore(_helpers.loadCore())
	s.importFile(writeFile(json.dumps(hostile)))
	a = s.getNote("a")
	R.check("SEG-05 names and titles limited, colours validated", len(s.folders[0]["name"]) == model.MAX_NAME and s.folders[0]["color"].startswith("#") and len(a["title"]) == model.MAX_TITLE)
	R.check("SEG-05 content above 1 MB dropped, tags limited, unknown lane replaced", a["content"] == "" and a["tags"] == ["x"] and a["laneId"] == "todo")
	R.check("SEG-05 references to unknown notebooks and folders removed", s.notebooks[0]["folderId"] is None and len(s.notebooks) == 1 and s.getNote("b")["notebookId"] is None)
	R.check("SEG-05 unknown fields are not kept", "__proto__" not in a and set(a) == {"id", "title", "content", "tags", "laneId", "notebookId", "folderId", "createdAt", "updatedAt"})
	R.check("SEG-05 wrong types become empty values", s.getNote("b")["title"] == "" and s.getNote("b")["content"] == "" and s.getNote("b")["tags"] == [])
	deep = writeFile("[" * 100000 + "]" * 100000)
	try:
		s.importFile(deep)
		R.check("SEG-05 deeply nested JSON refused", False, "accepted")
	except store.StoreError as e:
		R.check("SEG-05 deeply nested JSON refused without crashing", e.kind == "invalidImport", e.kind)
	except RecursionError:
		R.check("SEG-05 deeply nested JSON refused without crashing", False, "RecursionError")
	try:
		s.importFile(writeFile(b"\xff\xfe\x00garbage", binary=True))
		R.check("SEG-05 binary file refused", False, "accepted")
	except store.StoreError as e:
		R.check("SEG-05 binary file refused", e.kind == "invalidImport")

	# -- SEG-06 HTML ---------------------------------------------------------------------------------------
	typed = '<script>alert(1)</script> <img src=x onerror=alert(2)> "><iframe src=javascript:alert(3)>'
	html = markup.textToHtml(typed)
	R.check("SEG-06 what the person types is escaped in the HTML (safe when the web app opens it)", "<script" not in html and "<img" not in html and "<iframe" not in html and "&lt;script&gt;" in html, html)
	webHtml = '<p onclick="steal()">a<script>document.cookie</script><style>*{}</style><a href="javascript:alert(1)">link</a><iframe src="x">frame</iframe></p>'
	text = markup.htmlToText(webHtml)
	R.check("SEG-06 HTML from files: scripts, styles, frames and attributes dropped", text == "alink", text)
	R.check("SEG-06 the add-on never renders HTML (no wx.html, no browser)", not any(re.search(r"wx\.html|webbrowser|WebView", s) for s in sources.values()))

	# -- SEG-07 atomic write --------------------------------------------------------------------------------------
	s = _helpers.newStore(_helpers.loadCore())
	s.addNote("original")
	with open(s.path, "rb") as fh:
		before = fh.read()

	def failingOpen(path, *a, **k):
		if str(path).endswith(".tmp"):
			raise OSError("disk full")
		return realOpen(path, *a, **k)

	builtins.open = failingOpen
	try:
		try:
			s.addNote("nova")
			R.check("SEG-07 write error reported", False, "no error")
		except store.StoreError as e:
			R.check("SEG-07 write error reported", e.kind == "write")
	finally:
		builtins.open = realOpen
	with open(s.path, "rb") as fh:
		R.check("SEG-07 a failed write leaves the saved file untouched", fh.read() == before)
	R.check("SEG-07 no temporary file left behind", not os.path.exists(s.path + ".tmp"))
	storeSource = sources[os.path.join("addon", "globalPlugins", "NotasWorkflowNVDA", "store.py")]
	R.check("SEG-07 data flushed to disk and swapped with os.replace", "os.fsync" in storeSource and "os.replace(tmp, self.path)" in storeSource)

	# -- SEG-08 file names ---------------------------------------------------------------------------------------
	parent = _helpers.tempFolder()
	inner = os.path.join(parent, "data")
	os.makedirs(inner)
	s = store.NotesStore(inner)
	s.load()
	s.importFile(writeFile(json.dumps({"notes": [{"id": "../../evil", "title": "x"}, {"id": "ok", "title": "y"}], "notebooks": [{"id": "..\\x", "name": "n"}]})))
	R.check("SEG-08 data never decides a file name (nothing written outside the folder)", os.listdir(parent) == ["data"] and sorted(os.listdir(inner)) == [store.FILE_NAME] and [n["id"] for n in s.notes] == ["ok"], (os.listdir(parent), os.listdir(inner)))
	R.check("SEG-08 file name is fixed", store.FILE_NAME == "NotasWorkflowNVDA-data.json")
	with open(exported, encoding="utf-8") as fh:
		data = json.load(fh)
	R.check("SEG-08 export has only the notes (no settings, paths or user name)", set(data) == {"format", "version", "folders", "notebooks", "notes"} and folder not in json.dumps(data))

	# -- SEG-09 confirmations ---------------------------------------------------------------------------------------
	plugin_ = sources[os.path.join("addon", "globalPlugins", "NotasWorkflowNVDA", "__init__.py")]
	organize = sources[os.path.join("addon", "globalPlugins", "NotasWorkflowNVDA", "organizeDialog.py")]
	main = sources[os.path.join("addon", "globalPlugins", "NotasWorkflowNVDA", "mainDialog.py")]
	R.check("SEG-09 deleting a note, notebook or folder always asks, with No as the default", plugin_.count("wx.YES_NO | wx.NO_DEFAULT") == 1 and organize.count("wx.YES_NO | wx.NO_DEFAULT") == 1 and not re.search(r"store\.deleteNote\(", main + organize), "notes are deleted only through GlobalPlugin.deleteNote, which asks first")
	plugin = newPlugin()
	n = plugin.store.addNote("Fica")
	dlg = plugin.openWindow()
	dlg.refresh(n["id"])
	nvda_stubs.MESSAGEBOX_ANSWER["value"] = wx.CANCEL
	dlg.onDelete(None)
	R.check("SEG-09 any answer other than Yes keeps the note", plugin.store.getNote(n["id"]) is not None)
	nvda_stubs.MESSAGEBOX_ANSWER["value"] = wx.OK
	nb = plugin.store.addNotebook("C")
	plugin.store.moveNoteToNotebook(n["id"], nb["id"])
	plugin.store.deleteNotebook(nb["id"])
	R.check("SEG-09 deleting a notebook never deletes notes", plugin.store.getNote(n["id"]) is not None)

	# -- SEG-10 secure screens / SEG-11 uninstall ---------------------------------------------------------------------
	import globalPluginHandler
	import globalVars

	globalVars.appArgs.secure = True
	R.check("SEG-10 add-on disabled on secure screens", NotasWorkflowNVDA.disableInSecureMode(NotasWorkflowNVDA.GlobalPlugin) is globalPluginHandler.GlobalPlugin)
	globalVars.appArgs.secure = False
	R.check("SEG-11 uninstalling does not delete the notes (no uninstall task)", not os.path.exists(os.path.join(ADDON, "installTasks.py")) and not any("onUninstall" in s for s in sources.values()))
	R.check("SEG-11 the migration from NotasWorkflow 1.0.0 only copies (never moves or deletes the old notes)", "shutil.copy2" in "".join(sources.values()) and not any(re.search(r"shutil\.(move|rmtree)|os\.rename", s) for s in sources.values()))
	R.check("SEG-11 nothing deletes files except the add-on's own temporary file", all(m.group(0) == "os.remove(tmp)" for s in sources.values() for m in re.finditer(r"os\.(remove|unlink|rmdir)\([^)]*\)|shutil\.rmtree", s)))
	plugin.terminate()

	# -- SEG-12 static analysis (bandit) -------------------------------------------------------------------------------
	try:
		proc = subprocess.run([sys.executable, "-m", "bandit", "-q", "-r", ADDON, "-f", "json"], capture_output=True, text=True, timeout=300)  # nosec B603
		report = json.loads(proc.stdout or "{}")
		issues = [r for r in report.get("results", []) if r["issue_severity"] in ("MEDIUM", "HIGH")]
		R.check("SEG-12 bandit: no medium or high problems", "results" in report and not issues, [(i["test_id"], i["filename"], i["line_number"]) for i in issues] or proc.stderr[-300:])
		low = report.get("results", [])
		R.check("SEG-12 bandit: no low problems either", not low, [(i["test_id"], i["filename"], i["line_number"]) for i in low])
	except Exception as e:  # bandit missing
		R.check("SEG-12 bandit installed and ran", False, repr(e))


if __name__ == "__main__":
	try:
		run()
	except Exception:
		import traceback

		traceback.print_exc()
		R.check("suite finished without crashing", False, traceback.format_exc()[-800:])
	sys.exit(R.finish())
