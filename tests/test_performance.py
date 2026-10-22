# -*- coding: UTF-8 -*-
"""Performance tests (PERF-xx of docs/SDD-TESTES.md) with 100,000 notes in 80 notebooks
and 12 folders (tests/gerar_massa.py). The limits are generous (a busy computer must
not fail them) but far below what made NVDA stop answering before 1.2.0.

Run:  python tests/test_performance.py"""

import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from _guiapp import (  # noqa: E402
	NotasWorkflowNVDA, closeWindow, config, fakeModal, gui, noteDialog, organizeDialog, prompts, pump, replaced, searchDialog, store,
)
import _helpers  # noqa: E402
import gerar_massa  # noqa: E402
from _results import Recorder  # noqa: E402

R = Recorder("performance (test_performance)")
COUNT = 100000


def timed(func):
	start = time.perf_counter()
	result = func()
	return result, time.perf_counter() - start


def check(name, func, limit, plugin=None):
	"""Runs func after the previous write ended (as when the person waits for the answer)."""
	if plugin is not None:
		plugin.store.flush()
	result, elapsed = timed(func)
	print("   %6.2f s  %s" % (elapsed, name))
	R.check("%s (limit %.1f s)" % (name, limit), elapsed <= limit, "%.2f s" % elapsed)
	return result


def run():
	folder = _helpers.tempFolder()
	gerar_massa.gravar(gerar_massa.gerar(COUNT), os.path.join(folder, store.FILE_NAME))
	config.conf.spec[NotasWorkflowNVDA.CONFIG_SECTION] = NotasWorkflowNVDA.CONFIG_SPEC
	conf = config.conf[NotasWorkflowNVDA.CONFIG_SECTION]
	conf["dataFolder"] = folder
	conf["autoSaveSeconds"] = 1

	plugin = check("PERF-01 NVDA starts at once (notes read in the background)", NotasWorkflowNVDA.GlobalPlugin, 0.5)
	check("PERF-02 the %d notes are read" % COUNT, plugin.ensureLoaded, 20)
	R.check("PERF-02 every note was read", len(plugin.store.notes) == COUNT, len(plugin.store.notes))
	dlg = check("PERF-03 the window opens while the search is being prepared", plugin.openWindow, 3, plugin)
	check("PERF-04 the search is prepared in the background", lambda: plugin.indexReady.wait(180), 180)
	closeWindow()
	dlg = check("PERF-03 the window opens again at once (it is kept hidden)", plugin.openWindow, 0.5, plugin)
	todo, _cookie = dlg.tree.GetFirstChild(dlg.root)
	R.check("PERF-05 a lane shows one page, not 25,000 items", dlg.tree.GetChildrenCount(todo, False) <= 201, dlg.tree.GetChildrenCount(todo, False))
	# The lanes start closed: a note is chosen first, as the person does with the arrows.
	noteId = next(n["id"] for n in plugin.store.notes if n["laneId"] == "todo")
	dlg.refresh(noteId)
	R.check("PERF-05 the lanes start closed and the chosen note opens its lane", dlg.selectedNoteId() == noteId and dlg.tree.IsExpanded(dlg.laneNodes["todo"]) and not dlg.tree.IsExpanded(dlg.laneNodes["done"]))
	check("PERF-06 Alt+Shift+Arrow updates the task status", lambda: dlg.moveBy(1), 2, plugin)
	R.check("PERF-06 the status changed and the note stays selected", plugin.store.getNote(noteId)["laneId"] == "inprogress" and dlg.selectedNoteId() == noteId)
	check("PERF-07 a notebook filter is shown", lambda: dlg.setFilter(("notebook", plugin.store.notebooks[0]["id"])), 2, plugin)
	check("PERF-07 back to all notes", lambda: dlg.setFilter(("all", None)), 2, plugin)

	def edit(d):
		d.contentEdit.SetValue(d.contentEdit.GetValue() + "\nmais uma linha")
		d.finish()

	with fakeModal(noteDialog.NoteDialog, edit):
		check("PERF-08 open, edit and close a note (saves and updates the list)", lambda: dlg.openNote(noteId), 2, plugin)
	R.check("PERF-08 the edit was saved", plugin.store.getNote(noteId)["content"].endswith("<p>mais uma linha</p>"))
	_r, elapsed = timed(plugin.store.save)
	print("   %6.3f s  PERF-09 save" % elapsed)
	R.check("PERF-09 saving does not stop NVDA (written in the background, limit 0.1 s)", elapsed < 0.1, "%.3f s" % elapsed)
	check("PERF-09 the background write ends", plugin.store.flush, 15)
	sd = searchDialog.SearchDialog(gui.mainFrame, plugin)
	for query in ("genérico222", "nps cartoes", "ana souza whatsapp", "zzz"):
		sd.queryEdit.ChangeValue(query)
		found = check("PERF-10 search %r in %d notes" % (query, COUNT), lambda: sd.runSearch(announce=False), 2, plugin)
	R.check("PERF-10 the search finds the project by its name", any(n["title"].startswith("genérico222 ") for n, _s, _e in search_("genérico222", plugin)))
	sd.close()

	od = check("PERF-11 Notebooks and folders opens", lambda: organizeDialog.OrganizeDialog(gui.mainFrame, plugin), 3, plugin)
	od.Show()
	check("PERF-11 a notebook with its notes is opened in the tree", lambda: od.expandKey(("notebook", plugin.store.notebooks[0]["id"])), 2, plugin)
	check("PERF-11 the tree of notebooks and folders is rebuilt", od.refresh, 3, plugin)
	od.close()

	# PERF-14 export: the folder with the most notes, in one Word file and one Markdown file per note.
	s = plugin.store
	biggest = max(s.folders, key=lambda f: len(s.notesInFolder(f["id"])) + sum(len(s.notesIn(nb["id"])) for nb in s.notebooksIn(f["id"])))
	out = _helpers.tempFolder()
	for fmt, mode, label in ((0, 0, "one Word file"), (1, 1, "one Markdown file per note")):
		answers = [fmt, mode]
		with replaced(prompts, "chooseItem", lambda *a, **k: answers.pop(0)), replaced(prompts, "askSaveFile", lambda *a: os.path.join(out, "pasta.docx")), replaced(prompts, "askFolder", lambda *a: out):
			started = check("PERF-14 export of a folder (%s) does not stop NVDA" % label, lambda: plugin.exportItem(dlg, "folder", biggest["id"]), 1, plugin)
		_r, elapsed = timed(lambda: plugin.exportThread.join(120))
		print("   %6.2f s  PERF-14 written in the background (%s)" % (elapsed, label))
		R.check("PERF-14 the export (%s) ends in the background (limit 60 s)" % label, started and not plugin.exportThread.is_alive() and elapsed <= 60, "%.2f s" % elapsed)
	R.check("PERF-14 the files were written", os.path.getsize(os.path.join(out, "pasta.docx")) > 100000 and len(os.listdir(out)) == 2, os.listdir(out))
	check("PERF-12 the window closes", closeWindow, 2, plugin)
	_r, elapsed = timed(plugin.terminate)
	print("   %6.2f s  PERF-13 exit" % elapsed)
	R.check("PERF-13 NVDA exits with everything written (limit 20 s)", elapsed <= 20, "%.2f s" % elapsed)
	pump(timeout=0.2)


def search_(query, plugin):
	from NotasWorkflowNVDA import search

	return search.search(plugin.store.notes, query, index=plugin.searchIndex)


if __name__ == "__main__":
	try:
		run()
	except Exception:
		import traceback

		traceback.print_exc()
		R.check("suite finished without crashing", False, traceback.format_exc()[-800:])
	R.finish()
	sys.stdout.flush()
	# Python would take long to free 100,000 notes and the windows: the results are written.
	os._exit(1 if any(not ok for _n, ok, _i in R.results) else 0)
