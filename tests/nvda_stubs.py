# -*- coding: UTF-8 -*-
"""Minimal fakes of the NVDA modules used by NotasWorkflowNVDA, so the add-on can be
loaded and exercised outside NVDA (with a real wxPython).

gui.guiHelper is NVDA's real file (copied from the NVDA source, GPL-2), so the
dialogs are laid out exactly as in NVDA."""

import builtins
import gettext
import importlib.util
import inspect
import os
import re
import sys
import tempfile
import threading
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
RECORD = {"spoken": [], "messageBoxes": [], "settingsOpened": [], "log": [], "logErrors": []}
_lock = threading.Lock()
#: Answer that gui.messageBox returns (tests change it).
MESSAGEBOX_ANSWER = {"value": None}


def _module(name):
	mod = types.ModuleType(name)
	sys.modules[name] = mod
	return mod


def spoken():
	with _lock:
		return list(RECORD["spoken"])


def _defaultFromSpec(spec):
	m = re.search(r"default=([^,)]+)", spec)
	raw = m.group(1).strip() if m else ""
	if raw[:1] in ("'", '"'):
		return raw[1:-1]
	if spec.startswith("boolean"):
		return raw == "True"
	if spec.startswith("integer"):
		return int(raw)
	return raw


def install(configPath=None, withGui=True, secure=False):
	configPath = configPath or tempfile.mkdtemp(prefix="notasworkflownvda-test-")

	# addonHandler ------------------------------------------------------------
	addonHandler = _module("addonHandler")
	lang = os.environ.get("NOTASWORKFLOWNVDA_LANG")
	if lang and lang != "en":
		# Compiles the .po here: the .mo is a build product (not in git), so the
		# tests never depend on build.py having run before them.
		sys.path.insert(0, ROOT)
		import build

		localeDir = tempfile.mkdtemp(prefix="notasworkflownvda-locale-")
		os.makedirs(os.path.join(localeDir, lang, "LC_MESSAGES"))
		build.writeMo(build.parsePo(os.path.join(ROOT, "addon", "locale", lang, "LC_MESSAGES", "nvda.po")), os.path.join(localeDir, lang, "LC_MESSAGES", "nvda.mo"))
		translation = gettext.translation("nvda", localedir=localeDir, languages=[lang])
		gettextFunc = translation.gettext
	else:
		gettextFunc = lambda s: s  # noqa: E731

	def initTranslation():
		frame = inspect.currentframe().f_back
		frame.f_globals["_"] = gettextFunc

	addonHandler.initTranslation = initTranslation
	addonHandler.state = {}
	builtins._ = gettextFunc

	# globalVars ----------------------------------------------------------------
	globalVars = _module("globalVars")
	globalVars.appArgs = types.SimpleNamespace(configPath=configPath, secure=secure)

	# config ------------------------------------------------------------------
	config = _module("config")

	class Conf(dict):
		def __init__(self):
			super().__init__()
			self.spec = {}
			#: profiles[0] is the base configuration (nvda.ini) as NVDA reads it.
			self.profiles = [{}]

		def __getitem__(self, key):
			if not dict.__contains__(self, key):
				dict.__setitem__(self, key, {k: _defaultFromSpec(v) for k, v in self.spec[key].items()})
			return dict.__getitem__(self, key)

	config.conf = Conf()

	# ui / queueHandler / tones ---------------------------------------------------
	ui = _module("ui")

	def message(text, *a, **k):
		with _lock:
			RECORD["spoken"].append(text)

	ui.message = message
	queueHandler = _module("queueHandler")
	queueHandler.eventQueue = object()
	queueHandler.queueFunction = lambda queue, func, *args, **kwargs: func(*args, **kwargs)
	tones = _module("tones")
	tones.beep = lambda *a, **k: None

	# logHandler ---------------------------------------------------------------
	logHandler = _module("logHandler")

	class Log:
		def __getattr__(self, name):
			def f(msg, *a, **k):
				with _lock:
					RECORD["log"].append("%s: %s" % (name, msg))
					if name in ("error", "exception"):
						RECORD["logErrors"].append(str(msg))
			return f

	logHandler.log = Log()

	# scriptHandler ------------------------------------------------------------
	scriptHandler = _module("scriptHandler")

	def script(description=None, gesture=None, gestures=None, category=None, **kw):
		def deco(func):
			func.__doc__ = description
			func.gestures = ([gesture] if gesture else []) + list(gestures or [])
			func.category = category
			return func
		return deco

	scriptHandler.script = script

	# globalPluginHandler -------------------------------------------------------
	gph = _module("globalPluginHandler")

	class GlobalPlugin:
		def __init__(self):
			pass

		def terminate(self):
			pass

	gph.GlobalPlugin = GlobalPlugin

	if withGui:
		_installGui()
	return configPath


def _installGui():
	import wx

	MESSAGEBOX_ANSWER["value"] = wx.OK
	gui = _module("gui")
	spec = importlib.util.spec_from_file_location("gui.guiHelper", os.path.join(HERE, "nvda_real", "guiHelper.py"))
	guiHelper = importlib.util.module_from_spec(spec)
	sys.modules["gui.guiHelper"] = guiHelper
	spec.loader.exec_module(guiHelper)
	gui.guiHelper = guiHelper

	nvdaControls = _module("gui.nvdaControls")

	class SelectOnFocusSpinCtrl(wx.SpinCtrl):
		pass

	nvdaControls.SelectOnFocusSpinCtrl = SelectOnFocusSpinCtrl
	gui.nvdaControls = nvdaControls

	settingsDialogs = _module("gui.settingsDialogs")

	class SettingsPanel(wx.Panel):
		title = ""

		def __init__(self, parent):
			super().__init__(parent)
			sizer = wx.BoxSizer(wx.VERTICAL)
			self.settingsSizer = wx.BoxSizer(wx.VERTICAL)
			self.makeSettings(self.settingsSizer)
			sizer.Add(self.settingsSizer, flag=wx.ALL, border=5)
			self.SetSizer(sizer)

	class NVDASettingsDialog:
		categoryClasses = []

	settingsDialogs.SettingsPanel = SettingsPanel
	settingsDialogs.NVDASettingsDialog = NVDASettingsDialog
	gui.settingsDialogs = settingsDialogs

	def messageBox(message, caption="", style=wx.OK, parent=None):
		RECORD["messageBoxes"].append(message)
		return MESSAGEBOX_ANSWER["value"]

	gui.messageBox = messageBox

	class MainFrame(wx.Frame):
		def __init__(self):
			super().__init__(None, title="NVDA")
			self.sysTrayIcon = types.SimpleNamespace(toolsMenu=wx.Menu(), Bind=lambda *a, **k: None)

		def prePopup(self):
			pass

		def postPopup(self):
			pass

		def popupSettingsDialog(self, dialog, *args, **kwargs):
			RECORD["settingsOpened"].append((dialog, args))

	gui.MainFrame = MainFrame
	gui.mainFrame = None  # created by the test after wx.App exists
