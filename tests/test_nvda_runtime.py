# -*- coding: UTF-8 -*-
"""Checks against the NVDA installed on this computer (FUN-16 of docs/SDD-TESTES.md):
every module the add-on imports exists in NVDA's embedded Python (library.zip),
the NVDA functions it calls exist, and NVDA accepts the manifest versions.

When NVDA is not installed (for example on GitHub), the checks are reported as skipped.

Run:  python tests/test_nvda_runtime.py"""

import ast
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
ADDON = os.path.join(ROOT, "addon")
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import build  # noqa: E402
from _results import Recorder  # noqa: E402

R = Recorder("NVDA installed (test_nvda_runtime)")


def nvdaFolder():
	for base in (os.environ.get("ProgramFiles", ""), os.environ.get("ProgramFiles(x86)", "")):
		folder = os.path.join(base, "NVDA")
		if base and os.path.isfile(os.path.join(folder, "library.zip")):
			return folder
	return None


def nvdaVersion(folder):
	try:
		import ctypes
		from ctypes import wintypes

		path = os.path.join(folder, "nvda.exe")
		size = ctypes.windll.version.GetFileVersionInfoSizeW(path, None)
		buf = ctypes.create_string_buffer(size)
		ctypes.windll.version.GetFileVersionInfoW(path, 0, size, buf)
		value = ctypes.c_void_p()
		length = wintypes.UINT()
		ctypes.windll.version.VerQueryValueW(buf, "\\StringFileInfo\\040904B0\\ProductVersion", ctypes.byref(value), ctypes.byref(length))
		text = ctypes.wstring_at(value, length.value - 1)
		return tuple(int(x) for x in re.findall(r"\d+", text)[:3])
	except Exception:
		return None


def addonImports():
	mods = set()
	for folder, dirs, files in os.walk(ADDON):
		dirs[:] = [d for d in dirs if d != "__pycache__"]
		for f in files:
			if f.endswith(".py"):
				with open(os.path.join(folder, f), encoding="utf-8") as fh:
					tree = ast.parse(fh.read())
				for node in ast.walk(tree):
					if isinstance(node, ast.Import):
						mods.update(a.name for a in node.names)
					elif isinstance(node, ast.ImportFrom) and node.level == 0:
						mods.add(node.module)
						for a in node.names:
							mods.add(node.module + "." + a.name)
	return mods


def run():
	folder = nvdaFolder()
	if folder is None:
		R.check("FUN-16 NVDA not installed here: checks skipped", True)
		return
	z = zipfile.ZipFile(os.path.join(folder, "library.zip"))
	names = set(z.namelist())
	files = {n: None for n in names}

	def read(name):
		if files.get(name) is None:
			files[name] = z.read(name).decode("latin-1")
		return files[name]

	pyds = {f[:-4] for f in os.listdir(folder) if f.endswith(".pyd")}

	def exists(mod):
		path = mod.replace(".", "/")
		return (path + ".pyc") in names or (path + "/__init__.pyc") in names or mod in pyds or mod in sys.builtin_module_names

	missing = []
	attrsChecked = []
	for mod in sorted(addonImports()):
		if exists(mod):
			continue
		parent, _dot, attr = mod.rpartition(".")
		if parent and exists(parent):
			attrsChecked.append((parent, attr))
			continue
		missing.append(mod)
	R.check("FUN-16 every imported module exists in NVDA's Python", not missing, missing)
	needed = {
		"gui/guiHelper.pyc": ["BoxSizerHelper", "ButtonHelper", "BORDER_FOR_DIALOGS", "addLabeledControl", "addDialogDismissButtons"],
		"gui/nvdaControls.pyc": ["SelectOnFocusSpinCtrl"],
		"gui/settingsDialogs.pyc": ["SettingsPanel", "NVDASettingsDialog", "categoryClasses"],
		"gui/__init__.pyc": ["messageBox", "popupSettingsDialog", "prePopup", "postPopup", "sysTrayIcon"],
		"queueHandler.pyc": ["queueFunction", "eventQueue"],
		"globalVars.pyc": ["appArgs"],
		"config/__init__.pyc": ["profiles", "spec"],
		"scriptHandler.pyc": ["script"],
		"ui.pyc": ["message", "browseableMessage", "isHtml"],
		"addonHandler/__init__.pyc": ["initTranslation"],
	}
	absent = []
	for name, symbols in needed.items():
		if name not in names:
			alt = name.replace("/__init__.pyc", ".pyc")
			if alt in names:
				name = alt
			else:
				absent.append(name)
				continue
		text = read(name)
		absent += ["%s.%s" % (name, s) for s in symbols if s not in text]
	for parent, attr in attrsChecked:
		path = parent.replace(".", "/")
		name = path + ".pyc" if (path + ".pyc") in names else path + "/__init__.pyc"
		if name in names and attr not in read(name):
			absent.append("%s.%s" % (parent, attr))
	R.check("FUN-16 NVDA functions used by the add-on exist", not absent, absent)
	R.check("FUN-16 http.server not needed (NVDA may not ship it)", "http.server" not in addonImports())

	version = nvdaVersion(folder)
	man = build.readManifest()
	minimum = tuple(int(x) for x in man["minimumNVDAVersion"].split("."))
	tested = tuple(int(x) for x in man["lastTestedNVDAVersion"].split("."))
	if version:
		R.check("FUN-16 installed NVDA %s is not older than minimumNVDAVersion" % ".".join(map(str, version)), version >= minimum)
		# NVDA 2026.1 broke add-on compatibility: lastTested must be 2026.1 or later for NVDA 2026.x.
		backCompat = (version[0], 1, 0)
		R.check("FUN-16 NVDA %s accepts the add-on (lastTestedNVDAVersion %s)" % (".".join(map(str, version)), man["lastTestedNVDAVersion"]), tested >= backCompat)
	pyVersion = [f for f in os.listdir(folder) if re.fullmatch(r"python3\d+\.dll", f)]
	R.check("FUN-16 NVDA's Python version is covered by the unit tests (3.11 to 3.13)", pyVersion and pyVersion[0][7:9] in ("11", "12", "13"), pyVersion)


if __name__ == "__main__":
	try:
		run()
	except Exception:
		import traceback

		traceback.print_exc()
		R.check("suite finished without crashing", False, traceback.format_exc()[-500:])
	sys.exit(R.finish())
