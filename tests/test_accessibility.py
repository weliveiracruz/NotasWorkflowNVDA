# -*- coding: UTF-8 -*-
"""Accessibility tests (ACE-xx of docs/SDD-TESTES.md).

Besides the structure of the windows (labels, Alt shortcuts, tab order, focus),
on Windows it reads the accessible name of every control through MSAA
(oleacc), the same interface NVDA uses for these Win32 controls.

Run:  python tests/test_accessibility.py   (NOTASWORKFLOWNVDA_LANG=pt_BR for Portuguese)"""

import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from _guiapp import (  # noqa: E402
	VK_RETURN, Key, NotasWorkflowNVDA, closeWindow, fakeModal, gui, mark, newPlugin, noteDialog, openWindow,
	organizeDialog, postKey, prompts, pump, replaced, searchDialog, settingsPanel, spokenSince, wx,
)
from NotasWorkflowNVDA import messages  # noqa: E402
import _strings  # noqa: E402
import nvda_stubs  # noqa: E402
from _results import Recorder  # noqa: E402

LANG = os.environ.get("NOTASWORKFLOWNVDA_LANG", "en")
R = Recorder("accessibility (test_accessibility%s)" % ("" if LANG == "en" else ", " + LANG))
FOCUS = []
_originalSetFocus = wx.Window.SetFocus


def _recordFocus(self):
	FOCUS.append(self)
	return _originalSetFocus(self)


wx.Window.SetFocus = _recordFocus


def lastFocus():
	return FOCUS[-1] if FOCUS else None


def T(english):
	"""The text the user hears (translated when testing in Portuguese)."""
	return _(english)  # noqa: F821


def focusables(win):
	"""Controls reachable with Tab, in tab order (creation order of the children)."""
	out = []
	for c in win.GetChildren():
		if not c.IsShown() or not c.IsEnabled():
			continue
		if isinstance(c, (wx.StaticText, wx.StaticLine)):
			continue
		if isinstance(c, wx.Panel) and not c.AcceptsFocusFromKeyboard():
			out.extend(focusables(c))
		elif c.AcceptsFocusFromKeyboard():
			out.append(c)
	return out


def structuralName(ctrl):
	"""Name Windows gives: own label for buttons and check boxes, otherwise the
	static text that comes right before the control."""
	if isinstance(ctrl, (wx.Button, wx.CheckBox)):
		return ctrl.GetLabel()
	siblings = list(ctrl.GetParent().GetChildren())
	i = siblings.index(ctrl)
	j = i - 1
	while j >= 0 and not siblings[j].IsShown():
		j -= 1
	if j >= 0 and isinstance(siblings[j], wx.StaticText):
		return siblings[j].GetLabel()
	return ""


def mnemonicLabels(win):
	labels = []
	for c in win.GetChildren():
		if isinstance(c, (wx.Button, wx.CheckBox, wx.StaticText)) and c.IsShown():
			labels.append(c.GetLabel())
		if isinstance(c, wx.Panel):
			labels.extend(mnemonicLabels(c))
	return labels


def mnemonic(label):
	m = re.search(r"&([^&])", label.replace("&&", ""))
	return m.group(1).lower() if m else None


def plain(label):
	return label.replace("&&", "\0").replace("&", "").replace("\0", "&").rstrip(":").strip()


# -- MSAA (what NVDA reads) ------------------------------------------------------------------

_msaa = None


def _accessible(hwnd):
	ctypes, IAccessible = _msaa
	acc = ctypes.POINTER(IAccessible)()
	OBJID_CLIENT = ctypes.c_long(-4).value & 0xFFFFFFFF
	ctypes.oledll.oleacc.AccessibleObjectFromWindow(ctypes.c_void_p(hwnd), OBJID_CLIENT, ctypes.byref(IAccessible._iid_), ctypes.byref(acc))
	return acc


def msaaName(ctrl):
	"""Accessible name of a control read through oleacc, or None when MSAA is not available."""
	global _msaa
	if sys.platform != "win32":
		return None
	if _msaa is None:
		try:
			import ctypes

			import comtypes.client

			comtypes.client.GetModule("oleacc.dll")
			from comtypes.gen.Accessibility import IAccessible

			_msaa = (ctypes, IAccessible)
		except Exception:
			_msaa = False
	if not _msaa:
		return None
	ctypes = _msaa[0]
	# Read the window that really gets the focus with Tab (a spin control gives
	# the focus to its edit box, not to its arrows).
	_originalSetFocus(ctrl)
	wx.Yield()
	user32 = ctypes.windll.user32
	user32.GetFocus.restype = ctypes.c_void_p
	hwnd = user32.GetFocus() or ctrl.GetHandle()
	try:
		return _accessible(hwnd).accName(0) or ""
	except Exception:
		return ""


def msaaTreeSelection(tree):
	"""(name, state) of the selected tree item read through MSAA."""
	acc = _accessible(tree.GetHandle())
	child = acc.accSelection
	childId = child if isinstance(child, int) else 0
	return acc.accName(childId) or "", int(acc.accState(childId))


def checkWindow(name, win):
	ctrls = focusables(win)
	unnamed = [type(c).__name__ for c in ctrls if not structuralName(c).strip()]
	R.check("ACE-01 every focusable control has a name: %s" % name, not unnamed, unnamed)
	labels = [lbl for lbl in mnemonicLabels(win) if lbl.strip()]
	present = [k for k in (mnemonic(lbl) for lbl in labels) if k]
	dups = sorted({k for k in present if present.count(k) > 1})
	R.check("ACE-02 Alt shortcuts are unique: %s" % name, not dups, (dups, labels))
	missing = [c.GetLabel() for c in ctrls if isinstance(c, (wx.Button, wx.CheckBox)) and c.GetId() not in (wx.ID_OK, wx.ID_CANCEL) and not mnemonic(c.GetLabel())]
	R.check("ACE-02 every button has an Alt shortcut: %s" % name, not missing, missing)
	labelsWithout = [c.GetLabel() for c in win.GetChildren() if isinstance(c, wx.StaticText) and c.IsShown() and c.GetLabel().strip() and not mnemonic(c.GetLabel())]
	R.check("ACE-02 every field label has an Alt shortcut: %s" % name, not labelsWithout, labelsWithout)
	if isinstance(win, wx.TopLevelWindow):
		R.check("ACE-08 window has its own title: %s" % name, bool(win.GetTitle().strip()), win.GetTitle())
	if sys.platform == "win32" and ctrls and msaaName(ctrls[0]) is not None:
		wrong = []
		for c in ctrls:
			got = msaaName(c)
			expected = plain(structuralName(c))
			if not got or plain(got) != expected:
				wrong.append((type(c).__name__, expected, got))
		R.check("ACE-01 names read through MSAA (what NVDA says): %s" % name, not wrong, wrong)
	return ctrls


def defaultNvdaGestures():
	"""Keyboard gestures of the installed NVDA (scanned from library.zip) or, if
	NVDA is not installed, the NVDA+Alt gestures of NVDA 2026.1."""
	known = {"kb:nvda+alt+c", "kb:nvda+alt+m", "kb:nvda+alt+r", "kb:nvda+alt+s", "kb:nvda+alt+t", "kb:nvda+alt+home", "kb:nvda+alt+end", "kb:nvda+alt+tab"}
	found = set()
	for base in (os.environ.get("ProgramFiles(x86)", ""), os.environ.get("ProgramFiles", "")):
		lib = os.path.join(base, "NVDA", "library.zip")
		if base and os.path.isfile(lib):
			with zipfile.ZipFile(lib) as z:
				for n in z.namelist():
					if n.endswith(".pyc"):
						text = z.read(n).decode("latin-1")
						found.update(m.lower() for m in re.findall(r"kb(?:\([a-z]+\))?:[A-Za-z0-9+]+", text))
	return (found or known), bool(found)


def otherAddonGestures():
	"""Gestures declared by the other add-ons installed in this NVDA (if any)."""
	folder = os.path.join(os.environ.get("APPDATA", ""), "nvda", "addons")
	out = {}
	if not os.path.isdir(folder):
		return out
	for addon in os.listdir(folder):
		if addon.lower().startswith("notasworkflow"):
			continue
		for root, _dirs, files in os.walk(os.path.join(folder, addon)):
			for f in files:
				if f.endswith(".py"):
					try:
						with open(os.path.join(root, f), encoding="utf-8", errors="ignore") as fh:
							for g in re.findall(r"[\"'](kb(?:\([a-z]+\))?:[A-Za-z0-9+]+)[\"']", fh.read()):
								out.setdefault(_normalGesture(g), addon)
					except OSError:
						pass
	return out


def _normalGesture(g):
	head, _sep, keys = g.lower().partition(":")
	return head + ":" + "+".join(sorted(keys.split("+")))


def run():
	plugin = newPlugin()
	store = plugin.store
	dlg = openWindow(plugin)

	# -- main window, empty -----------------------------------------------------------------------
	ctrls = checkWindow("main window, no notes", dlg)
	R.check("ACE-04 without a note: Update the task status, Move to and Delete out of the tab order", ctrls == [dlg.filterChoice, dlg.tree, dlg.createButton, dlg.searchButton, dlg.organizeButton, dlg.exportButton, dlg.closeButton], [plain(structuralName(c)) for c in ctrls])
	R.check("ACE-06 focus starts on the notes", lastFocus() is dlg.tree, lastFocus())
	R.check("ACE-05 Esc closes the window", dlg.GetEscapeId() == wx.ID_CLOSE and dlg.closeButton.GetId() == wx.ID_CLOSE)
	R.check("ACE-03 a single view (lanes): no View box and no table", not hasattr(dlg, "viewChoice") and not hasattr(dlg, "table"))

	# -- notes ---------------------------------------------------------------------------------------
	nb = store.addNotebook("Trabalho & Casa")
	a = store.addNote("Planejar", notebookId=nb["id"])
	store.updateNote(a["id"], tags=["x", "y"])
	store.addNote("Revisar", "inprogress")
	dlg.refresh(a["id"])
	ctrls = checkWindow("main window, lanes", dlg)
	R.check("ACE-03 tab order: show, notes, create, update the task status, move to, delete, search, notebooks and folders, export, close", ctrls == [dlg.filterChoice, dlg.tree, dlg.createButton, dlg.statusButton, dlg.moveButton, dlg.deleteButton, dlg.searchButton, dlg.organizeButton, dlg.exportButton, dlg.closeButton], [plain(structuralName(c)) for c in ctrls])
	R.check("ACE-14 list label says what it shows and how many", plain(structuralName(dlg.tree)) == plain(T("Not&es: {filter} ({count})")).format(filter=T("All notes"), count=2), structuralName(dlg.tree))
	dlg.setFilter(("notebook", nb["id"]))
	label = structuralName(dlg.tree)
	R.check("ACE-14 & in a notebook name is read as & and does not become an Alt shortcut", "Trabalho & Casa" in plain(label) and mnemonic(label) == mnemonic(T("Not&es: {filter} ({count})")), label)
	dlg.setFilter(("all", None))
	dlg.refresh(a["id"])
	if msaaName(dlg.tree) is not None:
		R.check("ACE-14 list name read through MSAA", plain(msaaName(dlg.tree)) == plain(structuralName(dlg.tree)), msaaName(dlg.tree))
		dlg.refresh(a["id"])
		name, state = msaaTreeSelection(dlg.tree)
		expected = messages.noteDescription(a, messages.placeOf(store, a))
		R.check("ACE-18 selected note read by MSAA with title, place, tags and date", name == expected, (name, expected))
		lane = dlg.tree.GetItemParent(dlg.tree.GetSelection())
		dlg.tree.SelectItem(lane)
		name, state = msaaTreeSelection(dlg.tree)
		R.check("ACE-18 lane read by MSAA with name, number of notes and 'expanded'", name == messages.laneNode("todo", 1) and state & 0x200, (name, hex(state)))
		dlg.tree.SelectItem(dlg.tree.GetLastChild(lane))
	R.check("ACE-19 the status is said by its name, never only by its colour", all(not re.search(r"#[0-9A-Fa-f]{6}", dlg.tree.GetItemText(item)) for item in _allItems(dlg.tree)) and T("To do") in dlg.tree.GetItemText(dlg.tree.GetFirstChild(dlg.root)[0]))
	createLabels = messages.createLabels()
	present = [k for k in (mnemonic(lbl) for lbl in createLabels) if k]
	R.check("ACE-02 the Create menu items have unique Alt shortcuts", len(present) == 3 and len(set(present)) == 3, createLabels)

	# status and place: announced, focus stays
	dlg.refresh(a["id"])
	FOCUS.clear()
	n = mark()
	dlg.onKey(Key(wx.WXK_RIGHT, alt=True, shift=True))
	R.check("ACE-07 a status change is announced with the status name", spokenSince(n) == [messages.movedTo("inprogress")], spokenSince(n))
	R.check("ACE-06 focus stays on the note", lastFocus() is dlg.tree and dlg.selectedNoteId() == a["id"])
	FOCUS.clear()
	n = mark()
	with replaced(prompts, "chooseItem", lambda parent, message, caption, labels, current=0: 0):
		dlg.onMove(None)
	R.check("ACE-07 Move to is announced with the new place", spokenSince(n) == [messages.movedToPlace(messages.looseNote())], spokenSince(n))
	R.check("ACE-06 after Move to, the focus is back on the list", lastFocus() is dlg.tree)

	# Enter opens the note (real key press)
	opened = []
	with replaced(plugin, "editNote", lambda parent, noteId, **k: opened.append(noteId)):
		dlg.refresh(a["id"])
		postKey(dlg.tree, VK_RETURN)
		pump(lambda: opened, 2)
	R.check("ACE-05 Enter on a note of the list opens it", opened == [a["id"]], opened)

	# delete: focus to the neighbour
	nvda_stubs.MESSAGEBOX_ANSWER["value"] = wx.YES
	FOCUS.clear()
	dlg.onDelete(None)
	R.check("ACE-06 after deleting, focus on the list with a neighbour selected", lastFocus() is dlg.tree and dlg.selectedNoteId() is not None)
	nvda_stubs.MESSAGEBOX_ANSWER["value"] = wx.OK
	FOCUS.clear()
	dlg.onDelete(None)
	R.check("ACE-06 deleting the last note leaves the focus on the list", lastFocus() is dlg.tree)
	nvda_stubs.MESSAGEBOX_ANSWER["value"] = wx.OK

	# -- new note -------------------------------------------------------------------------------------
	nd = noteDialog.NewNoteDialog(dlg, store)
	nd.Show()
	ctrls = checkWindow("New note", nd)
	R.check("ACE-03 New note: title, location, status, create (disabled until there is a title), cancel", ctrls == [nd.titleEdit, nd.locationChoice, nd.laneChoice, nd.cancelButton], [plain(structuralName(c)) for c in ctrls])
	R.check("ACE-06 New note starts on the title", lastFocus() is nd.titleEdit)
	nd.titleEdit.SetValue("x")
	# Focusing a button (as the MSAA reading above does) makes it the temporary default:
	# check with the focus back on the title, where the person types.
	nd.titleEdit.SetFocus()
	wx.Yield()
	default = nd.GetDefaultItem()
	R.check("ACE-04 Create enters the tab order with a title and is the default button (Enter creates)", nd.createButton in focusables(nd) and default is not None and default.GetId() == nd.createButton.GetId(), default and default.GetLabel())
	nd.Destroy()

	# -- note window --------------------------------------------------------------------------------------
	note = store.addNote("Folha")
	seen = {}

	def inspect(d):
		d.Show()
		seen["focus"] = lastFocus()
		seen["ctrls"] = checkWindow("note window", d)
		seen["dlg"] = d
		seen["status"] = d.statusEdit.IsEditable()
		d.contentEdit.SetValue("abc")
		d.contentEdit.SetSelection(0, 3)
		seen["n"] = mark()
		d.applyFormat("italic")
		seen["spoken"] = spokenSince(seen["n"])
		d.finish()

	with fakeModal(noteDialog.NoteDialog, inspect):
		plugin.editNote(dlg, note["id"])
	d = seen["dlg"]
	R.check("ACE-03 note window: title, location, status, tags, content, formatting, save status, save and close", seen["ctrls"] == [d.titleEdit, d.locationChoice, d.laneChoice, d.tagsEdit, d.contentEdit, d.formatButton, d.statusEdit, d.saveButton], [plain(structuralName(c)) for c in seen["ctrls"]])
	R.check("ACE-06 opening a note starts on the title", seen["focus"] is d.titleEdit, seen["focus"])
	R.check("ACE-13 save status is read-only and reachable with Tab", seen["status"] is False)
	R.check("ACE-07 formatting is announced", seen["spoken"] == [T("Italic")], seen["spoken"])
	R.check("ACE-08 note window title is the note title", d.GetTitle() == "Folha")
	seen.clear()

	def remember(d):
		seen["focus"] = lastFocus()
		d.finish()

	with fakeModal(noteDialog.NewNoteDialog, lambda d: (d.titleEdit.SetValue("Nova"), wx.ID_OK)[1]), fakeModal(noteDialog.NoteDialog, remember):
		plugin.newNote(dlg)
	focus = seen.get("focus")
	R.check("ACE-06 after creating a note, the focus goes to its content", isinstance(focus, wx.TextCtrl) and focus.IsMultiLine(), focus)

	# -- search -------------------------------------------------------------------------------------------
	sd = searchDialog.SearchDialog(dlg, plugin)
	sd.Show()
	ctrls = checkWindow("Search notes", sd)
	R.check("ACE-03 Search: field, results, close (Open only with a result)", ctrls == [sd.queryEdit, sd.results, sd.closeButton], [plain(structuralName(c)) for c in ctrls])
	R.check("ACE-06 Search starts on the field", lastFocus() is sd.queryEdit)
	sd.queryEdit.SetValue("folha")
	FOCUS.clear()
	sd.onEnter(None)
	R.check("ACE-06 Enter in the field goes to the results", lastFocus() is sd.results)
	R.check("ACE-14 results label says how many", plain(structuralName(sd.results)) == plain(T("&Results ({count}):").format(count=1)), structuralName(sd.results))
	R.check("ACE-05 Esc closes the search", sd.GetEscapeId() == wx.ID_CLOSE)
	sd.close()

	# -- notebooks, folders and their notes ------------------------------------------------------------------
	inNb = store.addNote("No caderno", notebookId=nb["id"])
	od = organizeDialog.OrganizeDialog(dlg, plugin)
	od.Show()
	ctrls = checkWindow("Notebooks and folders", od)
	R.check("ACE-04 on Without folder: rename, move and delete out of the tab order", od.renameButton not in ctrls and od.deleteButton not in ctrls and od.moveButton not in ctrls)
	R.check("ACE-06 Notebooks and folders starts on the tree", lastFocus() is od.tree)
	od.expandKey(("notebook", nb["id"]))
	od.tree.SelectItem(od.nodes[("note", inNb["id"])])
	ctrls = focusables(od)
	R.check("ACE-03 on a note: tree, create, rename, move to, delete, close", ctrls == [od.tree, od.createButton, od.renameButton, od.moveButton, od.deleteButton, od.closeButton], [plain(structuralName(c)) for c in ctrls])
	if msaaName(od.tree) is not None:
		name, state = msaaTreeSelection(od.tree)
		R.check("ACE-18 note of the tree of notebooks read by MSAA with title and status", name == messages.noteDescription(inNb, "", withLane=True), name)
	opened = []
	with replaced(plugin, "editNote", lambda parent, noteId, **k: opened.append(noteId)):
		postKey(od.tree, VK_RETURN)
		pump(lambda: opened, 2)
	R.check("ACE-05 Enter on a note of the tree of notebooks opens it", opened == [inNb["id"]], opened)
	od.close()

	# -- settings panel -----------------------------------------------------------------------------------
	frame = wx.Frame(None, title="NVDA settings")
	panel = settingsPanel.NotasSettingsPanel(frame)
	frame.Fit()
	frame.Show()
	checkWindow("Settings panel", panel)
	R.check("ACE-08 settings category has a title", bool(panel.title))
	frame.Destroy()
	closeWindow()

	# -- commands -------------------------------------------------------------------------------------------
	scripts = [getattr(NotasWorkflowNVDA.GlobalPlugin, n) for n in dir(NotasWorkflowNVDA.GlobalPlugin) if n.startswith("script_")]
	R.check("ACE-10 every command has a description", all(s.__doc__ for s in scripts), [s.__name__ for s in scripts if not s.__doc__])
	R.check("ACE-10 commands are in the Notas Workflow NVDA category", NotasWorkflowNVDA.GlobalPlugin.scriptCategory == T("Notas Workflow NVDA"))
	ours = {}
	for s in scripts:
		for g in s.gestures:
			ours[_normalGesture(g)] = s.__name__
	R.check("ACE-09 three commands have a default shortcut (NVDA+Alt+N, F, B)", set(ours) == {"kb:alt+n+nvda", "kb:alt+f+nvda", "kb:alt+b+nvda"}, ours)
	defaults, scanned = defaultNvdaGestures()
	normalDefaults = {_normalGesture(g) for g in defaults}
	clash = sorted(g for g in ours if g in normalDefaults)
	R.check("ACE-09 no clash with NVDA's own commands%s" % (" (scanned from the installed NVDA)" if scanned else ""), not clash, clash)
	others = otherAddonGestures()
	clash = sorted("%s (%s)" % (g, others[g]) for g in ours if g in others)
	R.check("ACE-09 no clash with the other add-ons installed here", not clash, clash)

	# -- translations and documentation ------------------------------------------------------------------------
	missing = ["%s:%d" % (p, line) for p, line, _m, ok in _strings.translatable() if not ok]
	R.check("ACE-12 every translatable text has a Translators comment", not missing, missing)
	for docLang in ("en", "pt_BR"):
		path = os.path.join(HERE, "..", "addon", "doc", docLang, "readme.html")
		docHtml = ""
		if os.path.isfile(path):
			with open(path, encoding="utf-8") as f:
				docHtml = f.read()
		R.check("ACE-16 documentation %s has language, headings and real tables" % docLang, ('lang="%s"' % docLang.replace("_", "-")) in docHtml and "<h2>" in docHtml and "<th>" in docHtml)
	plugin.terminate()


def _allItems(tree):
	out = []

	def walk(node):
		child, cookie = tree.GetFirstChild(node)
		while child.IsOk():
			out.append(child)
			walk(child)
			child, cookie = tree.GetNextChild(node, cookie)

	walk(tree.GetRootItem())
	return out


if __name__ == "__main__":
	try:
		run()
	except Exception:
		import traceback

		traceback.print_exc()
		R.check("suite finished without crashing", False, traceback.format_exc()[-800:])
	sys.exit(R.finish())
