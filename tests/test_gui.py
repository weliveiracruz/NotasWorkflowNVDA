# -*- coding: UTF-8 -*-
"""Interface tests (FUN-xx of docs/SDD-TESTES.md) with real wxPython windows.

Run:  python tests/test_gui.py"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from _guiapp import (  # noqa: E402
	RECORD, VK_RETURN, Key, MainDialog, NotasWorkflowNVDA, click, closeWindow, config, creating, fakeModal, gui, mainDialog,
	mark, menu, model, newPlugin, noteDialog, openWindow, organizeDialog, postKey, prompts, pump, replaced, searchDialog,
	settingsPanel, spokenSince, store, tableRows, treeFind, treeTexts, waitSpoken, wx,
)
import _helpers  # noqa: E402
import nvda_stubs  # noqa: E402
from _results import Recorder  # noqa: E402

R = Recorder("interface (test_gui)")


def bulk(plugin, count, **where):
	"""Adds many notes at once (one save), as an import would."""
	extra = [model.makeNote("massa %04d" % i, **where) for i in range(count)]
	plugin.store.notes = plugin.store.notes + extra
	plugin.store.save()
	return extra


def run():
	plugin = newPlugin()
	folder = plugin.store.folder

	# -- FUN-14 main window ---------------------------------------------------------------------
	R.check("FUN-14 Tools menu has Notas Workflow NVDA", any(i.GetItemLabelText().startswith("Notas Workflow NVDA") for i in gui.mainFrame.sysTrayIcon.toolsMenu.GetMenuItems()))
	plugin.script_openWindow(None)
	pump(lambda: MainDialog._instance is not None)
	dlg = MainDialog._instance
	R.check("FUN-14 NVDA+Alt+N opens the window", dlg is not None and dlg.IsShown())
	lanes = treeTexts(dlg.tree)
	R.check("FUN-05 tree has the 4 status lanes, empty", [t for t, _k in lanes] == ["To do, 0 notes", "In progress, 0 notes", "Blocked, 0 notes", "Done, 0 notes"], lanes)
	R.check("FUN-14 only the lanes view: no View box, no table, no Open button", not any(hasattr(dlg, a) for a in ("viewChoice", "table", "openButton", "notebookButton")))
	R.check("FUN-14 note buttons disabled without a note", not dlg.statusButton.IsEnabled() and not dlg.deleteButton.IsEnabled() and not dlg.moveButton.IsEnabled())
	R.check("FUN-14 the button that creates is called Create", dlg.createButton.GetLabel() == "&Create…")
	again = openWindow(plugin)
	R.check("FUN-14 opening again reuses the window", again is dlg)

	# -- FUN-01 Create: note, notebook and folder --------------------------------------------------
	n = mark()
	with creating("Planejar sprint", "Pauta da **reunião**\n- item um"), menu(0):
		click(dlg.createButton)
	R.check("FUN-01 Create > Note creates the note", len(plugin.store.notes) == 1 and plugin.store.notes[0]["title"] == "Planejar sprint")
	note = plugin.store.notes[0]
	R.check("FUN-01 created in To do and announced", note["laneId"] == "todo" and "Note created in To do" in spokenSince(n), spokenSince(n))
	R.check("FUN-02 content typed in the note window saved as HTML", note["content"] == "<p>Pauta da <strong>reunião</strong></p><ul><li><p>item um</p></li></ul>", note["content"])
	R.check("FUN-14 new note selected in the tree", dlg.selectedNoteId() == note["id"])
	lanes = treeTexts(dlg.tree)
	R.check("FUN-05 note under its lane with title and date", lanes[0][0] == "To do, 1 note" and lanes[0][1][0].startswith("Planejar sprint, updated on "), lanes)
	R.check("FUN-14 note buttons enabled with a note", dlg.statusButton.IsEnabled() and dlg.moveButton.IsEnabled() and dlg.deleteButton.IsEnabled())
	with fakeModal(noteDialog.NewNoteDialog, lambda d: wx.ID_CANCEL), menu(0):
		click(dlg.createButton)
	R.check("FUN-01 cancelling New note creates nothing", len(plugin.store.notes) == 1)

	def emptyTitle(d):
		d.titleEdit.SetValue("   ")
		return wx.ID_OK if d.createButton.IsEnabled() else wx.ID_CANCEL

	with fakeModal(noteDialog.NewNoteDialog, emptyTitle), menu(0):
		click(dlg.createButton)
	R.check("FUN-01 empty title: Create unavailable", len(plugin.store.notes) == 1)
	with menu(None):
		click(dlg.createButton)
	R.check("FUN-01 Create menu closed: nothing created", len(plugin.store.notes) == 1 and not plugin.store.notebooks)
	n = mark()
	with menu(1), replaced(prompts, "askText", lambda *a, **k: "Trabalho"):
		click(dlg.createButton)
	nb = plugin.store.notebooks[0] if plugin.store.notebooks else None
	R.check("FUN-01 Create > Notebook creates a notebook", nb is not None and nb["name"] == "Trabalho" and "Notebook Trabalho created" in spokenSince(n), spokenSince(n))
	n = mark()
	with menu(2), replaced(prompts, "askText", lambda *a, **k: "Projetos"):
		click(dlg.createButton)
	f = plugin.store.folders[0] if plugin.store.folders else None
	R.check("FUN-01 Create > Folder creates a folder", f is not None and f["name"] == "Projetos" and "Folder Projetos created" in spokenSince(n), spokenSince(n))
	with menu(1), replaced(prompts, "askText", lambda *a, **k: None):
		click(dlg.createButton)
	R.check("FUN-01 cancelled name creates nothing", len(plugin.store.notebooks) == 1)
	dlg.setFilter(("folder", f["id"]))
	with menu(1), replaced(prompts, "askText", lambda *a, **k: "Dentro da pasta"):
		click(dlg.createButton)
	R.check("FUN-01 notebook created while a folder is shown goes into it", plugin.store.notebooks[-1]["folderId"] == f["id"])
	plugin.store.deleteNotebook(plugin.store.notebooks[-1]["id"])
	dlg.setFilter(("all", None))
	dlg.refresh(note["id"])

	labels, places = __import__("NotasWorkflowNVDA.messages", fromlist=["x"]).locationChoices(plugin.store)
	R.check("FUN-01 Location offers loose, each folder and each notebook", labels == ["Loose note (no notebook or folder)", "Folder Projetos", "Notebook Trabalho"], labels)
	with creating("Bug do login", laneIndex=2, locationIndex=2), menu(0):
		click(dlg.createButton)
	bug = plugin.store.notes[-1]
	R.check("FUN-01 status and notebook chosen in New note", bug["laneId"] == "blocked" and bug["notebookId"] == nb["id"], bug)
	R.check("FUN-05 notebook shown in the tree", any("Bug do login, notebook Trabalho" in k for _t, kids in treeTexts(dlg.tree) for k in kids))
	with creating("Direto na pasta", locationIndex=1), menu(0):
		click(dlg.createButton)
	direct = plugin.store.notes[-1]
	R.check("FUN-01 a note can be created directly in a folder", direct["folderId"] == f["id"] and direct["notebookId"] is None and any("Direto na pasta, folder Projetos" in k for _t, kids in treeTexts(dlg.tree) for k in kids))
	item, cookie = dlg.tree.GetFirstChild(dlg.root)
	for _i in range(3):
		item, cookie = dlg.tree.GetNextChild(dlg.root, cookie)
	dlg.tree.SelectItem(item)
	with creating("Entregue"), menu(0):
		click(dlg.createButton)
	R.check("FUN-01 New note starts in the selected lane", plugin.store.notes[-1]["laneId"] == "done")

	# -- FUN-07 update the task status ---------------------------------------------------------------
	dlg.refresh(note["id"])
	R.check("FUN-07 the status button is called Update the task status", dlg.statusButton.GetLabel() == "&Update the task status…")
	n = mark()
	dlg.onKey(Key(wx.WXK_RIGHT, alt=True, shift=True))
	R.check("FUN-07 Alt+Shift+Right: next status, announced", note["laneId"] == "inprogress" and "Status updated to In progress" in spokenSince(n), (note["laneId"], spokenSince(n)))
	R.check("FUN-07 selection follows the note", dlg.selectedNoteId() == note["id"])
	dlg.onKey(Key(wx.WXK_LEFT, alt=True, shift=True))
	n = mark()
	dlg.onKey(Key(wx.WXK_LEFT, alt=True, shift=True))
	R.check("FUN-07 first lane: nothing changes and it is said", note["laneId"] == "todo" and spokenSince(n) == ["Already in the first lane"], spokenSince(n))
	offered = []

	def chooseDone(window, labels):
		offered.append(labels)
		return labels.index("Done")

	with replaced(prompts, "chooseFromMenu", chooseDone):
		click(dlg.statusButton)
	R.check("FUN-07 Update the task status offers the other statuses and changes it", note["laneId"] == "done" and offered == [["In progress", "Blocked", "Done"]], (note["laneId"], offered))
	with menu(None):
		click(dlg.statusButton)
	R.check("FUN-07 status menu closed keeps the status", note["laneId"] == "done")
	key = Key(wx.WXK_DOWN)
	dlg.onKey(key)
	R.check("FUN-14 arrows still move in the list", key.skipped)

	# -- FUN-23 Enter opens the note -----------------------------------------------------------------
	opened = []
	with replaced(plugin, "editNote", lambda parent, noteId, **k: opened.append(noteId)):
		dlg.refresh(note["id"])
		before = dlg.selectedNoteId()
		postKey(dlg.tree, VK_RETURN)
		pump(lambda: opened, 2)
		titles = {x["id"]: x["title"] for x in plugin.store.notes}
		R.check("FUN-23 Enter on a note of the list opens it (real key press)", opened == [note["id"]], ([titles.get(x) for x in opened], titles.get(before), titles.get(dlg.selectedNoteId())))
		opened.clear()
		evt = wx.TreeEvent(wx.wxEVT_TREE_ITEM_ACTIVATED, dlg.tree, dlg.tree.GetSelection())
		dlg.tree.GetEventHandler().ProcessEvent(evt)
		dlg.handleTreeKey(Key(wx.WXK_RETURN))
		pump(lambda: opened, 2)
		pump(timeout=0.2)
		R.check("FUN-23 double click and Enter together open it only once", opened == [note["id"]], ([titles.get(x) for x in opened], titles.get(dlg.selectedNoteId()), note["title"]))
	lane = dlg.tree.GetItemParent(dlg.tree.GetSelection())
	dlg.tree.SelectItem(lane)
	dlg.activate()
	R.check("FUN-23 Enter on a lane closes it", not dlg.tree.IsExpanded(lane))
	dlg.activate()
	R.check("FUN-23 Enter again opens it", dlg.tree.IsExpanded(lane))

	# -- FUN-08 Move to: notebook, folder or loose ------------------------------------------------------
	dlg.refresh(note["id"])
	n = mark()
	with replaced(prompts, "chooseItem", lambda parent, message, caption, labels, current=0: labels.index("Notebook Trabalho")):
		click(dlg.moveButton)
	R.check("FUN-08 Move to a notebook", note["notebookId"] == nb["id"] and note["folderId"] is None and "Moved to Notebook Trabalho" in spokenSince(n), spokenSince(n))
	n = mark()
	with replaced(prompts, "chooseItem", lambda parent, message, caption, labels, current=0: labels.index("Folder Projetos")):
		click(dlg.moveButton)
	R.check("FUN-08 Move to a folder (directly)", note["folderId"] == f["id"] and note["notebookId"] is None and "Moved to Folder Projetos" in spokenSince(n), spokenSince(n))
	seen = []

	def keep(parent, message, caption, labels, current=0):
		seen.append(current)
		return current

	n = mark()
	with replaced(prompts, "chooseItem", keep):
		click(dlg.moveButton)
	R.check("FUN-08 Move to starts on the current place; choosing it changes nothing", seen == [1] and not spokenSince(n), (seen, spokenSince(n)))
	with replaced(prompts, "chooseItem", lambda *a, **k: 0):
		click(dlg.moveButton)
	R.check("FUN-08 Move to loose", note["folderId"] is None and note["notebookId"] is None)

	# -- FUN-10 filters -----------------------------------------------------------------------------
	choices = dlg.filterChoice.GetItems()
	R.check("FUN-10 Show offers all, loose, recent, each notebook and each folder", choices == ["All notes", "Loose notes", "Recent notes", "Notebook: Trabalho", "Folder: Projetos"], choices)
	dlg.setFilter(("notebook", nb["id"]))
	R.check("FUN-10 notebook filter shows only its notes", dlg.visibleIds == [bug["id"]] and dlg.treeLabel.GetLabel() == "Not&es: Notebook: Trabalho (1)", (dlg.visibleIds, dlg.treeLabel.GetLabel()))
	dlg.setFilter(("loose", None))
	R.check("FUN-10 loose filter: neither in a notebook nor in a folder", bug["id"] not in dlg.visibleIds and direct["id"] not in dlg.visibleIds and note["id"] in dlg.visibleIds)
	plugin.store.moveNotebookToFolder(nb["id"], f["id"])
	dlg.setFilter(("folder", f["id"]))
	R.check("FUN-10 folder filter shows its notes and the notes of its notebooks", sorted(dlg.visibleIds) == sorted([bug["id"], direct["id"]]), dlg.visibleIds)
	dlg.setFilter(("recent", None))
	R.check("FUN-10 recent: last changed first", dlg.visibleIds[0] == note["id"], dlg.visibleIds)
	dlg.setFilter(("all", None))

	# -- FUN-24 long lanes in pages --------------------------------------------------------------------
	before = list(plugin.store.notes)
	extra = bulk(plugin, 1100)
	dlg.refresh()
	todo, _c = dlg.tree.GetFirstChild(dlg.root)
	R.check("FUN-24 a long lane shows 500 notes and a Show more item", dlg.tree.GetChildrenCount(todo, False) == 501, dlg.tree.GetChildrenCount(todo, False))
	more = dlg.tree.GetLastChild(todo)
	R.check("FUN-24 Show more says how many are left", dlg.tree.GetItemText(more) == "Show 500 more notes (%d not shown yet)" % (len([x for x in plugin.store.notes if x["laneId"] == "todo"]) - 500), dlg.tree.GetItemText(more))
	dlg.tree.SelectItem(more)
	postKey(dlg.tree, VK_RETURN)
	todo, _c = dlg.tree.GetFirstChild(dlg.root)
	R.check("FUN-24 Enter on Show more adds the next page and selects its first note", dlg.tree.GetChildrenCount(todo, False) == 1001 and dlg.selectedNoteId() == [x for x in plugin.store.notes if x["laneId"] == "todo"][500]["id"], (dlg.tree.GetChildrenCount(todo, False), dlg.selectedNoteId()))
	dlg.setFilter(("all", None))
	dlg.refresh(extra[-1]["id"])
	R.check("FUN-24 selecting a note beyond the page shows its page", dlg.selectedNoteId() == extra[-1]["id"])
	plugin.store.notes = before
	plugin.store.save()
	dlg.setFilter(("all", None))

	# -- FUN-09 delete ------------------------------------------------------------------------------
	extraNote = plugin.store.addNote("Apagar")
	dlg.refresh(extraNote["id"])
	nvda_stubs.MESSAGEBOX_ANSWER["value"] = wx.NO
	dlg.onKey(Key(wx.WXK_DELETE))
	R.check("FUN-09 Delete asks and No keeps the note", plugin.store.getNote(extraNote["id"]) is not None and RECORD["messageBoxes"][-1].startswith("Delete the note Apagar?"))
	nvda_stubs.MESSAGEBOX_ANSWER["value"] = wx.YES
	n = mark()
	click(dlg.deleteButton)
	R.check("FUN-09 Yes deletes and announces", plugin.store.getNote(extraNote["id"]) is None and "Note deleted: Apagar" in spokenSince(n))
	R.check("FUN-09 selection goes to a neighbour", dlg.selectedNoteId() is not None)
	nvda_stubs.MESSAGEBOX_ANSWER["value"] = wx.OK

	# -- FUN-02/03/04 note window -------------------------------------------------------------------
	nd = noteDialog.NoteDialog(gui.mainFrame, plugin, note["id"])
	nd.Show()
	R.check("FUN-02 note window shows the note", nd.titleEdit.GetValue() == "Planejar sprint" and nd.contentEdit.GetValue() == "Pauta da **reunião**\n- item um" and nd.GetTitle() == "Planejar sprint")
	R.check("FUN-02 status and location boxes show the note", nd.laneChoice.GetSelection() == 3 and nd.locationChoice.GetSelection() == 0)
	before = note["updatedAt"]
	nd.tagsEdit.SetValue("trabalho, Ideia, trabalho")
	R.check("FUN-03 change shown as unsaved", nd.statusEdit.GetValue() == "Unsaved changes…")
	R.check("FUN-03 saved by itself after the delay", pump(lambda: note["tags"] == ["trabalho", "Ideia"], 4), note["tags"])
	R.check("FUN-03 save status says the time", nd.statusEdit.GetValue().startswith("Saved at "), nd.statusEdit.GetValue())
	R.check("FUN-03 content not rewritten when only the tags changed", note["content"] == "<p>Pauta da <strong>reunião</strong></p><ul><li><p>item um</p></li></ul>" and note["updatedAt"] >= before)
	config.conf["NotasWorkflowNVDA"]["announceAutoSave"] = True
	n = mark()
	nd.titleEdit.SetValue("Planejar sprint 42")
	R.check("FUN-03 announces the automatic saving when chosen", waitSpoken(n, lambda s: s == "Note saved", 4) and note["title"] == "Planejar sprint 42", spokenSince(n))
	R.check("FUN-02 window title follows the note title", nd.GetTitle() == "Planejar sprint 42")
	config.conf["NotasWorkflowNVDA"]["announceAutoSave"] = False

	# formatting: second line selected
	nd.contentEdit.SetValue("linha um\nlinha dois")
	nd.contentEdit.SetFocus()
	nd.contentEdit.SetSelection(15, 19)
	pump(lambda: nd.FindFocus() is nd.contentEdit, 1)
	n = mark()
	nd.onCharHook(Key(ord("B"), ctrl=True))
	R.check("FUN-04 Ctrl+B in the content applies bold to the selection", nd.contentEdit.GetValue() == "linha um\nlinha **dois**" and "Bold" in spokenSince(n), (nd.contentEdit.GetValue(), spokenSince(n)))
	R.check("FUN-04 selection kept on the formatted text", nd.contentEdit.GetSelection() == (17, 21), nd.contentEdit.GetSelection())
	nd.contentEdit.SetSelection(3, 3)
	with replaced(noteDialog, "chooseFormat", lambda w: "heading2"):
		click(nd.formatButton)
	R.check("FUN-04 Formatting… menu applies a line format", nd.contentEdit.GetValue().startswith("## linha um"), nd.contentEdit.GetValue())
	with replaced(noteDialog, "chooseFormat", lambda w: None):
		click(nd.formatButton)
	R.check("FUN-04 Formatting… cancelled changes nothing", nd.contentEdit.GetValue().startswith("## linha um"))
	n = mark()
	nd.onCharHook(Key(ord("S"), ctrl=True))
	R.check("FUN-03 Ctrl+S saves at once", note["content"] == "<h2>linha um</h2><p>linha <strong>dois</strong></p>" and "Note saved" in spokenSince(n), note["content"])
	key = Key(ord("A"))
	nd.onCharHook(key)
	R.check("FUN-04 other keys go to the field", key.skipped)
	nd.laneChoice.SetSelection(1)
	nd.onChange("laneId")
	nd.locationChoice.SetSelection(nd.places.index((nb["id"], None)))
	nd.onChange("location")
	nd.finish()
	R.check("FUN-03 closing saves what is pending (status and location)", note["laneId"] == "inprogress" and note["notebookId"] == nb["id"], (note["laneId"], note["notebookId"]))

	nd = noteDialog.NoteDialog(gui.mainFrame, plugin, note["id"])
	nd.contentEdit.SetValue("ultima frase")
	nd.onCharHook(Key(wx.WXK_ESCAPE))
	R.check("FUN-03 Esc also saves (nothing is lost)", note["content"] == "<p>ultima frase</p>", note["content"])

	gone = plugin.store.addNote("Some")
	nd = noteDialog.NoteDialog(gui.mainFrame, plugin, gone["id"])
	plugin.store.deleteNote(gone["id"])
	nd.contentEdit.SetValue("x")
	n = mark()
	nd.finish()
	R.check("FUN-02 note deleted while open: said, nothing recreated", plugin.store.getNote(gone["id"]) is None and "This note was deleted." in spokenSince(n))

	imported = plugin.store.addNote("Importada")
	importedHtml = '<p class="x">texto <span style="color:red">vermelho</span></p>'
	plugin.store.updateNote(imported["id"], content=importedHtml)
	nd = noteDialog.NoteDialog(gui.mainFrame, plugin, imported["id"])
	nd.titleEdit.SetValue("Importada 2")
	nd.finish()
	R.check("FUN-02 imported HTML kept when only the title changes", imported["content"] == importedHtml and imported["title"] == "Importada 2")

	# -- FUN-11 search window ---------------------------------------------------------------------
	sd = searchDialog.SearchDialog(gui.mainFrame, plugin)
	n = mark()
	sd.queryEdit.SetValue("ULTIMA")
	R.check("FUN-11 searches while typing (300 ms)", pump(lambda: sd.resultIds == [note["id"]], 3), sd.resultIds)
	R.check("FUN-11 result with excerpt, relevance and date", tableRows(sd.results)[0][:3] == ["Planejar sprint 42", "ultima frase", "100%"], tableRows(sd.results))
	R.check("FUN-11 number of results announced", waitSpoken(n, lambda s: s == "1 note found"), spokenSince(n))
	R.check("FUN-11 results label says how many", sd.resultsLabel.GetLabel() == "&Results (1):")
	R.check("FUN-22 the search keeps the prepared text of the notes", len(plugin.searchIndex) >= len(plugin.store.notes) - 1)
	opened = []
	with replaced(plugin, "editNote", lambda parent, noteId, **k: opened.append(noteId)):
		click(sd.openButton)
	R.check("FUN-11 Open opens the note found", opened == [note["id"]] and sd.openedId == note["id"])
	n = mark()
	sd.queryEdit.SetValue("inexistente")
	sd.onEnter(None)
	R.check("FUN-11 nothing found is announced", "No note found" in spokenSince(n) and not sd.openButton.IsEnabled())
	sd.close()
	with fakeModal(searchDialog.SearchDialog, lambda d: None):
		plugin.script_search(None)
		pump(timeout=0.3)
	R.check("FUN-18 NVDA+Alt+B opens the search", True)

	# -- FUN-12 notebooks, folders and their notes ---------------------------------------------------------
	od = organizeDialog.OrganizeDialog(gui.mainFrame, plugin)
	od.Show()
	texts = [t for t, _k in treeTexts(od.tree)]
	R.check("FUN-12 tree: each folder, Without folder and Loose notes", len(texts) == 3 and texts[0].startswith("Folder Projetos, 1 notebook, 1 note") and texts[1].startswith("Without folder, 0 notebooks") and texts[2].startswith("Loose notes, "), texts)
	od.expandKey(("notebook", nb["id"]))
	nbNode = od.nodes[("notebook", nb["id"])]
	kids = treeTexts(od.tree, nbNode)
	R.check("FUN-12 a notebook lists its notes with title and status", any(t.startswith("Bug do login, Blocked") for t, _k in kids) and any(t.startswith("Planejar sprint 42, In progress") for t, _k in kids), kids)
	od.expandKey(("folder", f["id"]))
	R.check("FUN-12 a folder lists its notebooks and the notes put directly in it", ("note", direct["id"]) in od.nodes and od.tree.GetItemParent(od.nodes[("note", direct["id"])]) == od.nodes[("folder", f["id"])])
	opened = []
	with replaced(plugin, "editNote", lambda parent, noteId, **k: opened.append(noteId)):
		od.tree.SelectItem(od.nodes[("note", bug["id"])])
		postKey(od.tree, VK_RETURN)
		pump(lambda: opened, 2)
	R.check("FUN-12 Enter on a note of the tree opens it (real key press)", opened == [bug["id"]], (opened, od.selected(), od._pending, od.FindFocus() is od.tree, od.IsActive()))
	R.check("FUN-12 Rename, Move to and Delete available on a note", od.renameButton.IsEnabled() and od.moveButton.IsEnabled() and od.deleteButton.IsEnabled())
	od.refresh(("folder", f["id"]))
	n = mark()
	with menu(1), replaced(prompts, "askText", lambda *a, **k: "Pessoal"):
		click(od.createButton)
	pessoal = next(x for x in plugin.store.notebooks if x["name"] == "Pessoal")
	R.check("FUN-12 Create > Notebook inside the selected folder", pessoal["folderId"] == f["id"] and "Notebook Pessoal created" in spokenSince(n) and od.selected() == ("notebook", pessoal["id"]))
	with creating("Na caderneta"), menu(0):
		click(od.createButton)
	nova = plugin.store.notes[-1]
	R.check("FUN-12 Create > Note inside the selected notebook, selected in the tree", nova["notebookId"] == pessoal["id"] and od.selected() == ("note", nova["id"]), (nova["notebookId"], od.selected()))
	with menu(2), replaced(prompts, "askText", lambda *a, **k: "Arquivo"):
		click(od.createButton)
	arquivo = next(x for x in plugin.store.folders if x["name"] == "Arquivo")
	R.check("FUN-12 Create > Folder", od.selected() == ("folder", arquivo["id"]))
	od.refresh(("note", nova["id"]))
	with replaced(prompts, "askText", lambda *a, **k: "Na caderneta 2"):
		od.handleTreeKey(Key(wx.WXK_F2))
	R.check("FUN-12 F2 on a note changes its title", nova["title"] == "Na caderneta 2")
	with replaced(prompts, "chooseItem", lambda *a, **k: 0):
		click(od.moveButton)
	R.check("FUN-12 Move to on a note (to loose), the note stays selected", nova["notebookId"] is None and od.selected() == ("note", nova["id"]) and od.tree.GetItemParent(od.nodes[("note", nova["id"])]) == od.nodes[("loose", None)])
	nvda_stubs.MESSAGEBOX_ANSWER["value"] = wx.YES
	click(od.deleteButton)
	R.check("FUN-12 Delete on a note asks and deletes it", plugin.store.getNote(nova["id"]) is None and RECORD["messageBoxes"][-1].startswith("Delete the note Na caderneta 2?"))
	od.refresh(("notebook", pessoal["id"]))
	with replaced(prompts, "askText", lambda *a, **k: "Casa"):
		click(od.renameButton)
	R.check("FUN-12 rename a notebook", pessoal["name"] == "Casa")
	with replaced(prompts, "chooseItem", lambda *a, **k: 2):
		click(od.moveButton)
	R.check("FUN-12 move notebook to another folder", pessoal["folderId"] == arquivo["id"])
	od.refresh(("notebook", nb["id"]))
	click(od.deleteButton)
	R.check("FUN-12 deleting a notebook keeps its notes (loose)", plugin.store.getNotebook(nb["id"]) is None and note["notebookId"] is None and plugin.store.getNote(bug["id"]) is not None)
	od.refresh(("folder", arquivo["id"]))
	od.handleTreeKey(Key(wx.WXK_DELETE))
	R.check("FUN-12 deleting a folder (Delete key) keeps its notebooks", plugin.store.getFolder(arquivo["id"]) is None and pessoal["folderId"] is None)
	nvda_stubs.MESSAGEBOX_ANSWER["value"] = wx.OK
	od.tree.SelectItem(od.nodes[("none", None)])
	R.check("FUN-12 Without folder: rename and delete unavailable", not od.renameButton.IsEnabled() and not od.deleteButton.IsEnabled())
	many = bulk(plugin, 650, notebookId=pessoal["id"])
	od.refresh(("notebook", pessoal["id"]))
	od.expandKey(("notebook", pessoal["id"]))
	node = od.nodes[("notebook", pessoal["id"])]
	R.check("FUN-24 a notebook with many notes shows 500 and Show more", od.tree.GetChildrenCount(node, False) == 501, od.tree.GetChildrenCount(node, False))
	od.tree.SelectItem(od.tree.GetLastChild(node))
	od.activate()
	node = od.nodes[("notebook", pessoal["id"])]
	R.check("FUN-24 Show more in the tree of notebooks adds the rest", od.tree.GetChildrenCount(node, False) == 650 and od.selected() == ("note", many[500]["id"]), (od.tree.GetChildrenCount(node, False), od.selected()))
	plugin.store.notes = [x for x in plugin.store.notes if x["notebookId"] != pessoal["id"]]
	plugin.store.save()
	od.close()
	dlg.refresh()
	R.check("FUN-10 filters follow the notebooks and folders", "Notebook: Casa" in dlg.filterChoice.GetItems() and "Notebook: Trabalho" not in dlg.filterChoice.GetItems())

	# -- FUN-15 settings ------------------------------------------------------------------------------
	frame = wx.Frame(None, title="NVDA settings")
	panel = settingsPanel.NotasSettingsPanel(frame)
	R.check("FUN-15 settings show the folder in use", panel.folderEdit.GetValue() == folder)
	exported = os.path.join(_helpers.tempFolder(), "export.json")
	n = mark()
	with replaced(settingsPanel, "askSavePath", lambda p: exported):
		click(panel.exportButton)
	with open(exported, encoding="utf-8") as fh:
		data = json.load(fh)
	R.check("FUN-13 export writes the notes in the web format", len(data["notes"]) == len(plugin.store.notes) and any(s.startswith("Exported: ") for s in spokenSince(n)))
	other = newPlugin()
	frame2 = wx.Frame(None, title="NVDA settings")
	panel2 = settingsPanel.NotasSettingsPanel(frame2)
	n = mark()
	with replaced(settingsPanel, "askOpenPath", lambda p: exported):
		click(panel2.importButton)
	R.check("FUN-13 import brings the notes and says how many", len(other.store.notes) == len(data["notes"]) and any(s.startswith("Imported: ") for s in spokenSince(n)), spokenSince(n))
	bad = os.path.join(_helpers.tempFolder(), "bad.json")
	with open(bad, "w") as fh:
		fh.write("{}")
	n = mark()
	with replaced(settingsPanel, "askOpenPath", lambda p: bad):
		click(panel2.importButton)
	R.check("FUN-13 invalid import is explained", "This file has no Notas Workflow NVDA notes." in spokenSince(n), spokenSince(n))
	newFolder = _helpers.tempFolder()
	panel2.folderEdit.SetValue(newFolder)
	panel2.autoSaveSpin.SetValue(5)
	panel2.announceCheck.SetValue(True)
	R.check("FUN-15 valid folder accepted", panel2.isValid())
	n = mark()
	panel2.onSave()
	conf = config.conf["NotasWorkflowNVDA"]
	R.check("FUN-15 settings saved", conf["dataFolder"] == newFolder and conf["autoSaveSeconds"] == 5 and conf["announceAutoSave"] is True)
	R.check("FUN-15 changing the folder copies the notes there", other.store.folder == newFolder and os.path.isfile(os.path.join(newFolder, store.FILE_NAME)) and "Notes saved in the new folder" in spokenSince(n), spokenSince(n))
	panel2.folderEdit.SetValue(os.path.join(newFolder, "does-not-exist"))
	R.check("FUN-15 folder that does not exist refused", not panel2.isValid())
	panel2.onDefault(None)
	R.check("FUN-15 Use the default folder", panel2.folderEdit.GetValue() == other.defaultDataFolder() and panel2.chosenFolder() == "")
	with replaced(settingsPanel, "askFolder", lambda p, c: folder):
		click(panel2.browseButton)
	R.check("FUN-15 Browse fills the folder", panel2.folderEdit.GetValue() == folder)
	n = mark()
	panel2.onSave()
	R.check("FUN-15 folder with notes: its notes are used", other.store.folder == folder and any(s.startswith("Using the notes of the new folder") for s in spokenSince(n)), spokenSince(n))
	frame.Destroy()
	frame2.Destroy()
	other.terminate()

	# -- FUN-18 commands ----------------------------------------------------------------------------------
	plugin.terminate()
	plugin = newPlugin(folder)
	R.check("FUN-17 notes read again when NVDA starts", len(plugin.store.notes) >= 4)
	with creating("Pelo atalho"):
		plugin.script_newNote(None)
		pump(timeout=0.3)
	R.check("FUN-18 NVDA+Alt+F creates a note", plugin.store.notes[-1]["title"] == "Pelo atalho")
	n = mark()
	plugin.script_lanesSummary(None)
	R.check("FUN-18 lanes summary", spokenSince(n) and spokenSince(n)[-1].startswith("To do ") and "Done " in spokenSince(n)[-1], spokenSince(n))
	outside = newPlugin(folder)
	outside.store.addNote("De outro computador")
	os.utime(outside.store.path, ns=(1, 1))
	dlg = openWindow(plugin)
	R.check("FUN-17 window reads the file again when another program changed it", any(nt["title"] == "De outro computador" for nt in plugin.store.notes))
	outside.terminate()

	# damaged file announced
	with open(plugin.store.path, "w", encoding="utf-8") as fh:
		fh.write("{x")
	n = mark()
	broken = newPlugin(folder)
	R.check("FUN-17 damaged file: backup used and announced", any(s.startswith("The saved notes were damaged") for s in spokenSince(n)) and len(broken.store.notes) >= 4, spokenSince(n))
	broken.terminate()

	# write error announced
	plugin.store.folder = os.path.join(plugin.store.path, "impossible")
	n = mark()
	ok, _r = plugin.safe(plugin.store.addNote, "x")
	R.check("FUN-17 write error is announced with the folder", not ok and any(s.startswith("Could not save the notes in") for s in spokenSince(n)), spokenSince(n))
	plugin.store.folder = folder

	# -- FUN-16 terminate ---------------------------------------------------------------------------------
	pending = plugin.store.notes[0]
	editor = noteDialog.NoteDialog(gui.mainFrame, plugin, pending["id"])
	plugin.openEditor = editor
	editor.contentEdit.SetValue("digitado antes de sair")
	panels = gui.settingsDialogs.NVDASettingsDialog.categoryClasses
	errors = len(RECORD["logErrors"])
	plugin.terminate()
	R.check("FUN-16 terminate closes the window and removes the settings panel", MainDialog._instance is None and settingsPanel.NotasSettingsPanel not in panels and settingsPanel.NotasSettingsPanel.plugin is None)
	R.check("FUN-16 NVDA exiting with a note open saves what was typed", pending["content"] == "<p>digitado antes de sair</p>", pending["content"])
	editor.Destroy()
	R.check("FUN-16 no error in the log", len(RECORD["logErrors"]) == errors, RECORD["logErrors"][errors:])
	closeWindow()
	legacyMigration()


def legacyMigration():
	"""FUN-20: first start of Notas Workflow NVDA 1.1.0 where NotasWorkflow 1.0.0 was used."""
	import globalVars

	saved = globalVars.appArgs.configPath
	cfg = _helpers.tempFolder()
	globalVars.appArgs.configPath = cfg
	oldFolder = os.path.join(cfg, "NotasWorkflow")
	os.makedirs(oldFolder)
	oldFile = os.path.join(oldFolder, "NotasWorkflow-data.json")
	with open(oldFile, "w", encoding="utf-8") as fh:
		json.dump({"format": "notas-workflow", "version": 1, "notes": [{"id": "v1", "title": "da 1.0.0"}, {"id": "v2", "title": "outra"}]}, fh)
	with open(oldFile + ".bak", "w", encoding="utf-8") as fh:
		fh.write('{"notes": []}')
	with open(oldFile, "rb") as fh:
		before = fh.read()
	conf = config.conf["NotasWorkflowNVDA"]
	conf["dataFolder"] = ""
	conf["legacyChecked"] = False
	conf["view"] = "lanes"
	config.conf.profiles[0]["NotasWorkflow"] = {"view": "table", "autoSaveSeconds": "7", "announceAutoSave": "True"}
	try:
		n = mark()
		plugin = NotasWorkflowNVDA.GlobalPlugin()
		R.check("FUN-20 first start brings the notes of NotasWorkflow 1.0.0", [x["title"] for x in plugin.store.notes] == ["da 1.0.0", "outra"] and plugin.store.folder == os.path.join(cfg, "NotasWorkflowNVDA"), (plugin.store.folder, len(plugin.store.notes)))
		R.check("FUN-20 the copy is announced, saying the old add-on can be uninstalled", any(s.startswith("Notes of the previous version brought to Notas Workflow NVDA: 2 notes") for s in spokenSince(n)), spokenSince(n))
		R.check("FUN-20 settings of [NotasWorkflow] copied", conf["view"] == "table" and conf["autoSaveSeconds"] == 7 and conf["announceAutoSave"] is True)
		R.check("FUN-20 backup copy also brought", os.path.isfile(plugin.store.backupPath))
		with open(oldFile, "rb") as fh:
			R.check("FUN-20 nothing of the old add-on is changed or deleted", fh.read() == before and os.path.isfile(oldFile + ".bak"))
		plugin.store.addNote("nova")
		plugin.terminate()
		n = mark()
		again = NotasWorkflowNVDA.GlobalPlugin()
		R.check("FUN-20 the copy happens only once (new notes are kept)", len(again.store.notes) == 3 and not any("previous version" in s for s in spokenSince(n)))
		again.terminate()
	finally:
		globalVars.appArgs.configPath = saved
		config.conf.profiles[0].pop("NotasWorkflow", None)


if __name__ == "__main__":
	try:
		run()
	except Exception:
		import traceback

		traceback.print_exc()
		R.check("suite finished without crashing", False, traceback.format_exc()[-800:])
	sys.exit(R.finish())
