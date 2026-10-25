# -*- coding: UTF-8 -*-
"""Unit tests of the core (FUN-xx of docs/SDD-TESTES.md), without NVDA and without wx.
Run with Python 3.11 and 3.13:  python tests/_run_unittest.py"""

import datetime
import json
import os
import py_compile
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import _helpers  # noqa: E402

core = _helpers.loadCore()
model, markup, search, store, exporter = core.model, core.markup, core.search, core.store, core.exporter


def newStore(folder=None):
	return _helpers.newStore(core, folder)


class FUN01_CreateNote(unittest.TestCase):
	def test_defaults_like_the_web_app(self):
		s = newStore()
		n = s.addNote("  Reunião  ")
		self.assertEqual(n["title"], "Reunião")
		self.assertEqual(n["laneId"], "todo")
		self.assertIsNone(n["notebookId"])
		self.assertIsNone(n["folderId"])
		self.assertEqual(n["content"], "")
		self.assertEqual(n["tags"], [])
		self.assertEqual(n["createdAt"], n["updatedAt"])
		self.assertEqual(set(n), {"id", "title", "content", "tags", "laneId", "notebookId", "folderId", "createdAt", "updatedAt"})

	def test_lane_and_notebook(self):
		s = newStore()
		nb = s.addNotebook("Trabalho")
		n = s.addNote("x", "blocked", nb["id"])
		self.assertEqual((n["laneId"], n["notebookId"]), ("blocked", nb["id"]))

	def test_unknown_lane_and_notebook_are_refused(self):
		s = newStore()
		n = s.addNote("x", "nope", "missing-notebook")
		self.assertEqual((n["laneId"], n["notebookId"]), ("todo", None))

	def test_title_is_limited_and_single_line(self):
		s = newStore()
		n = s.addNote("a\nb\tc\x00" + "x" * 500)
		self.assertNotIn("\n", n["title"])
		self.assertNotIn("\x00", n["title"])
		self.assertEqual(len(n["title"]), model.MAX_TITLE)

	def test_ids_are_uuid4_and_unique(self):
		s = newStore()
		ids = {s.addNote("x")["id"] for _ in range(50)}
		self.assertEqual(len(ids), 50)
		self.assertTrue(all(model.isValidId(i) and len(i) == 36 for i in ids))

	def test_new_notes_go_to_the_end(self):
		s = newStore()
		a, b = s.addNote("a"), s.addNote("b")
		self.assertEqual([n["id"] for n in s.notes], [a["id"], b["id"]])


class FUN02_EditNote(unittest.TestCase):
	def test_update_changes_updatedAt_only_when_something_changed(self):
		s = newStore()
		n = s.addNote("a")
		n["updatedAt"] = "2020-01-01T00:00:00.000Z"
		self.assertFalse(s.updateNote(n["id"], title="a"))
		self.assertEqual(n["updatedAt"], "2020-01-01T00:00:00.000Z")
		self.assertTrue(s.updateNote(n["id"], title="b"))
		self.assertNotEqual(n["updatedAt"], "2020-01-01T00:00:00.000Z")

	def test_tags_are_cleaned(self):
		s = newStore()
		n = s.addNote("a")
		s.updateNote(n["id"], tags=" Trabalho, ideia ,, trabalho, " + "z" * 80)
		self.assertEqual(n["tags"], ["Trabalho", "ideia", "z" * model.MAX_TAG])

	def test_tags_limit(self):
		s = newStore()
		n = s.addNote("a")
		s.updateNote(n["id"], tags=["t%d" % i for i in range(100)])
		self.assertEqual(len(n["tags"]), model.MAX_TAGS)

	def test_invalid_lane_and_notebook_ignored(self):
		s = newStore()
		n = s.addNote("a", "done")
		s.updateNote(n["id"], laneId="weird", notebookId="ghost")
		self.assertEqual((n["laneId"], n["notebookId"]), ("done", None))

	def test_content_limit(self):
		s = newStore()
		n = s.addNote("a")
		s.updateNote(n["id"], content="x" * (model.MAX_CONTENT + 10))
		self.assertEqual(len(n["content"]), model.MAX_CONTENT)

	def test_missing_note(self):
		s = newStore()
		with self.assertRaises(store.StoreError) as cm:
			s.updateNote("nope", title="x")
		self.assertEqual(cm.exception.kind, "notFound")

	def test_change_is_saved_to_the_file(self):
		folder = _helpers.tempFolder()
		s = newStore(folder)
		n = s.addNote("a")
		s.updateNote(n["id"], title="b", content="<p>c</p>")
		again = newStore(folder)
		self.assertEqual((again.notes[0]["title"], again.notes[0]["content"]), ("b", "<p>c</p>"))


class FUN04_Formatting(unittest.TestCase):
	def test_bold_wraps_and_unwraps(self):
		text, s, e, applied = markup.applyFormat("ola mundo", 4, 9, "bold")
		self.assertEqual((text, s, e, applied), ("ola **mundo**", 6, 11, True))
		self.assertEqual(markup.applyFormat(text, s, e, "bold"), ("ola mundo", 4, 9, False))
		self.assertEqual(markup.applyFormat("ola **mundo**", 4, 13, "bold"), ("ola mundo", 4, 9, False))

	def test_empty_selection_puts_the_cursor_between_the_marks(self):
		self.assertEqual(markup.applyFormat("ab", 1, 1, "italic"), ("a**b", 2, 2, True))

	def test_every_inline_mark(self):
		for kind, mark in (("italic", "*"), ("strike", "~~"), ("code", "`")):
			self.assertEqual(markup.applyFormat("x y", 2, 3, kind)[0], "x %sy%s" % (mark, mark))

	def test_line_formats(self):
		self.assertEqual(markup.applyFormat("a\nb\nc", 2, 2, "heading2")[0], "a\n## b\nc")
		self.assertEqual(markup.applyFormat("a\n## b", 3, 3, "heading3")[0], "a\n### b")
		self.assertEqual(markup.applyFormat("a\nb", 0, 3, "bullet")[0], "- a\n- b")
		self.assertEqual(markup.applyFormat("- a\n- b", 0, 7, "bullet")[0:2], ("a\nb", 0))
		self.assertEqual(markup.applyFormat("a\nb\nc", 0, 5, "ordered")[0], "1. a\n2. b\n3. c")
		self.assertEqual(markup.applyFormat("a", 0, 0, "quote")[0], "> a")
		self.assertEqual(markup.applyFormat("> a", 0, 0, "quote")[0], "a")

	def test_divider_on_its_own_line(self):
		self.assertEqual(markup.applyFormat("ab", 1, 1, "divider")[0], "a\n---\nb")
		self.assertEqual(markup.applyFormat("", 0, 0, "divider")[0], "---\n")

	def test_out_of_range_selection(self):
		self.assertEqual(markup.applyFormat("ab", 5, -3, "bold")[0], "**ab**")

	def test_formats_match_the_web_toolbar(self):
		self.assertEqual(markup.FORMATS, ("bold", "italic", "strike", "code", "heading2", "heading3", "bullet", "ordered", "quote", "divider"))
		with self.assertRaises(ValueError):
			markup.applyFormat("a", 0, 0, "underline")


class FUN05_MarkupAndHtml(unittest.TestCase):
	SAMPLE = "# Título\n\nlinha **negrito** e *itálico* 2*3*4 <script>\n- a\n- b\n3. x\n4. y\n> citação\n> \n---\n```\ncódigo <b>\n```\n~~riscado~~ `c*d*`"

	def test_round_trip_without_loss(self):
		self.assertEqual(markup.htmlToText(markup.textToHtml(self.SAMPLE)), self.SAMPLE)

	def test_tiptap_html(self):
		h = markup.textToHtml("## T\n- a\n1. b\n> q\n---\n**x** *y* ~~z~~ `w`")
		self.assertEqual(h, "<h2>T</h2><ul><li><p>a</p></li></ul><ol><li><p>b</p></li></ol><blockquote><p>q</p></blockquote><hr><p><strong>x</strong> <em>y</em> <s>z</s> <code>w</code></p>")

	def test_lines_are_paragraphs_and_blank_lines_empty_paragraphs(self):
		self.assertEqual(markup.textToHtml("a\n\nb"), "<p>a</p><p></p><p>b</p>")
		self.assertEqual(markup.textToHtml(""), "")
		self.assertEqual(markup.htmlToText(""), "")

	def test_text_is_escaped(self):
		h = markup.textToHtml('<img src=x onerror=alert(1)> & "x"')
		self.assertNotIn("<img", h)
		self.assertIn("&lt;img", h)
		self.assertIn("&amp;", h)

	def test_html_of_the_web_editor(self):
		h = "<h3>Pauta</h3><p>Olá <b>mundo</b> <i>x</i><br>linha 2</p><ul><li><p>um</p><ul><li><p>sub</p></li></ul></li></ul><ol start=\"5\"><li><p>cinco</p></li></ol><pre><code>a\nb</code></pre>"
		self.assertEqual(markup.htmlToText(h), "### Pauta\nOlá **mundo** *x*\nlinha 2\n- um\n  - sub\n5. cinco\n```\na\nb\n```")

	def test_script_style_and_unknown_tags(self):
		h = "<p>a<script>alert(1)</script><style>p{}</style><span class=x onclick=y>b</span><custom>c</custom></p>"
		self.assertEqual(markup.htmlToText(h), "abc")
		self.assertEqual(markup.plainText(h), "abc")

	def test_entities(self):
		self.assertEqual(markup.htmlToText("<p>&lt;x&gt; &amp; &eacute; &#233;</p>"), "<x> & é é")

	def test_plain_text_content(self):
		self.assertEqual(markup.htmlToText("só texto &amp; mais\nlinha"), "só texto & mais\nlinha")

	def test_plain_and_preview(self):
		h = markup.textToHtml("## Título\n- **item** um\n\n" + "palavra " * 50)
		self.assertEqual(markup.plainText(h).splitlines()[:2], ["Título", "item um"])
		self.assertEqual(len(markup.preview(h)), 100)
		self.assertNotIn("\n", markup.preview(h))

	def test_broken_html_does_not_crash(self):
		for h in ("<p>a", "</p></ul></blockquote>b", "<ol start='99999999999999'><li>x</li></ol>", "<<<>>>", "<p" * 1000):
			self.assertIsInstance(markup.htmlToText(h), str)


class FUN06_Lanes(unittest.TestCase):
	def test_lanes_of_the_web_app(self):
		self.assertEqual(model.LANE_IDS, ("todo", "inprogress", "blocked", "done"))
		self.assertEqual([lane["color"] for lane in model.LANES], ["#007AFF", "#FF9500", "#FF2D55", "#34C759"])

	def test_neighbour_lane(self):
		self.assertEqual(model.neighbourLane("todo", 1), "inprogress")
		self.assertEqual(model.neighbourLane("done", -1), "blocked")
		self.assertIsNone(model.neighbourLane("todo", -1))
		self.assertIsNone(model.neighbourLane("done", 1))

	def test_by_lane_keeps_the_order(self):
		s = newStore()
		a, b, c = s.addNote("a"), s.addNote("b", "done"), s.addNote("c")
		lanes = model.byLane(s.notes)
		self.assertEqual([n["id"] for n in lanes["todo"]], [a["id"], c["id"]])
		self.assertEqual([n["id"] for n in lanes["done"]], [b["id"]])
		self.assertEqual(lanes["blocked"], [])

	def test_move(self):
		s = newStore()
		n = s.addNote("a")
		self.assertTrue(s.moveNote(n["id"], "inprogress"))
		self.assertEqual(n["laneId"], "inprogress")
		self.assertFalse(s.moveNote(n["id"], "inprogress"))
		self.assertFalse(s.moveNote(n["id"], "nope"))


class FUN30_OrderInLane(unittest.TestCase):
	def test_place_beside_moves_only_the_order(self):
		s = newStore()
		a, b, c, d = s.addNote("a"), s.addNote("b", "done"), s.addNote("c"), s.addNote("d")
		stamp = c["updatedAt"]
		self.assertTrue(s.placeNoteBeside(c["id"], a["id"], after=False))
		self.assertEqual([n["title"] for n in s.notes], ["c", "a", "b", "d"])
		self.assertEqual([n["title"] for n in model.byLane(s.notes)["todo"]], ["c", "a", "d"])
		self.assertEqual(c["updatedAt"], stamp)
		self.assertTrue(s.placeNoteBeside(c["id"], d["id"], after=True))
		self.assertEqual([n["title"] for n in s.notes], ["a", "b", "d", "c"])
		self.assertTrue(s.placeNoteBeside(c["id"], d["id"], after=False))
		self.assertEqual([n["title"] for n in s.notes], ["a", "b", "c", "d"])

	def test_already_there_or_itself_changes_nothing(self):
		s = newStore()
		a, b = s.addNote("a"), s.addNote("b")
		self.assertFalse(s.placeNoteBeside(a["id"], b["id"], after=False))
		self.assertFalse(s.placeNoteBeside(b["id"], a["id"], after=True))
		self.assertFalse(s.placeNoteBeside(a["id"], a["id"], after=True))
		self.assertEqual([n["title"] for n in s.notes], ["a", "b"])
		self.assertEqual(s.getNote(b["id"]), b)

	def test_unknown_note(self):
		s = newStore()
		a = s.addNote("a")
		with self.assertRaises(store.StoreError):
			s.placeNoteBeside(a["id"], "nope", after=True)

	def test_order_is_saved(self):
		folder = _helpers.tempFolder()
		s = newStore(folder)
		a, b = s.addNote("a"), s.addNote("b")
		s.placeNoteBeside(b["id"], a["id"], after=False)
		again = newStore(folder)
		self.assertEqual([n["title"] for n in again.notes], ["b", "a"])


class FUN07_Filters(unittest.TestCase):
	def setUp(self):
		s = self.s = newStore()
		self.folder = s.addFolder("Projetos")
		self.nbIn = s.addNotebook("Dentro", self.folder["id"])
		self.nbOut = s.addNotebook("Fora")
		self.loose = s.addNote("solta")
		self.inside = s.addNote("dentro", notebookId=self.nbIn["id"])
		self.outside = s.addNote("fora", notebookId=self.nbOut["id"])
		self.direct = s.addNote("pasta direta", folderId=self.folder["id"])

	def ids(self, flt):
		return [n["id"] for n in self.s.filtered(flt)]

	def test_all_loose_notebook_folder(self):
		self.assertEqual(len(self.ids(model.FILTER_ALL)), 4)
		self.assertEqual(self.ids(model.FILTER_LOOSE), [self.loose["id"]], "loose: neither in a notebook nor in a folder")
		self.assertEqual(self.ids(("notebook", self.nbOut["id"])), [self.outside["id"]])
		self.assertEqual(self.ids(("folder", self.folder["id"])), [self.inside["id"], self.direct["id"]])

	def test_recent_are_the_10_changed_last(self):
		s = newStore()
		notes = [s.addNote("n%d" % i) for i in range(15)]
		for i, n in enumerate(notes):
			n["updatedAt"] = "2026-01-%02dT00:00:00.000Z" % (i + 1)
		recent = s.filtered(model.FILTER_RECENT)
		self.assertEqual([n["title"] for n in recent], ["n%d" % i for i in range(14, 4, -1)])


class FUN08_DeleteNote(unittest.TestCase):
	def test_delete(self):
		s = newStore()
		a, b = s.addNote("a"), s.addNote("b")
		s.deleteNote(a["id"])
		self.assertEqual(s.notes, [b])
		with self.assertRaises(store.StoreError):
			s.deleteNote(a["id"])


class FUN09_NotebooksAndFolders(unittest.TestCase):
	def test_colors_rotate_like_the_web_app(self):
		s = newStore()
		colors = [s.addNotebook("n%d" % i)["color"] for i in range(7)]
		self.assertEqual(colors, list(model.NOTEBOOK_COLORS) + [model.NOTEBOOK_COLORS[0]])
		self.assertEqual(s.addFolder("f")["color"], model.FOLDER_COLORS[0])

	def test_deleting_a_notebook_keeps_its_notes(self):
		s = newStore()
		nb = s.addNotebook("x")
		n = s.addNote("a", notebookId=nb["id"])
		s.deleteNotebook(nb["id"])
		self.assertEqual(s.notes, [n])
		self.assertIsNone(n["notebookId"])

	def test_deleting_a_folder_keeps_notebooks_and_notes(self):
		s = newStore()
		f = s.addFolder("f")
		nb = s.addNotebook("x", f["id"])
		n = s.addNote("a")
		n["folderId"] = f["id"]
		s.deleteFolder(f["id"])
		self.assertEqual((nb["folderId"], n["folderId"], len(s.notebooks), len(s.notes)), (None, None, 1, 1))

	def test_rename_move_and_empty_names(self):
		s = newStore()
		f = s.addFolder("f")
		nb = s.addNotebook("x")
		s.renameNotebook(nb["id"], "  y ")
		s.renameFolder(f["id"], "g")
		s.moveNotebookToFolder(nb["id"], f["id"])
		self.assertEqual((nb["name"], f["name"], nb["folderId"]), ("y", "g", f["id"]))
		s.moveNotebookToFolder(nb["id"], None)
		self.assertIsNone(nb["folderId"])
		for call in (lambda: s.addNotebook("  "), lambda: s.addFolder(""), lambda: s.renameNotebook(nb["id"], "\n")):
			with self.assertRaises(store.StoreError) as cm:
				call()
			self.assertEqual(cm.exception.kind, "emptyName")
		with self.assertRaises(store.StoreError):
			s.moveNotebookToFolder(nb["id"], "ghost")

	def test_notebook_in_unknown_folder_is_loose(self):
		s = newStore()
		self.assertIsNone(s.addNotebook("x", "ghost")["folderId"])


class FUN10_Search(unittest.TestCase):
	def setUp(self):
		s = self.s = newStore()
		self.a = s.addNote("Reunião de ação")
		s.updateNote(self.a["id"], content=markup.textToHtml("Pauta: **orçamento** do projeto"), tags=["Trabalho"])
		self.b = s.addNote("Lista de compras")
		s.updateNote(self.b["id"], content=markup.textToHtml("pão, café, reunião às 10h"))

	def test_ignores_accents_and_case(self):
		found = search.search(self.s.notes, "ACAO")
		self.assertEqual([n["id"] for n, _s, _e in found], [self.a["id"]])
		self.assertEqual([n["id"] for n, _s, _e in search.search(self.s.notes, "orcamento")], [self.a["id"]])

	def test_score_is_terms_found_over_terms(self):
		found = {n["id"]: score for n, score, _e in search.search(self.s.notes, "reuniao cafe")}
		self.assertEqual(found[self.a["id"]], 0.5)
		self.assertEqual(found[self.b["id"]], 1.0)

	def test_title_breaks_ties(self):
		found = search.search(self.s.notes, "reuniao")
		self.assertEqual(found[0][0]["id"], self.a["id"])

	def test_tags_are_searched(self):
		self.assertEqual(len(search.search(self.s.notes, "trabalho")), 1)

	def test_markup_is_not_searched(self):
		self.assertEqual(search.search(self.s.notes, "strong"), [])
		self.assertEqual(search.search(self.s.notes, "**"), [])

	def test_empty_query(self):
		self.assertEqual(search.search(self.s.notes, "   "), [])
		self.assertEqual(search.search(self.s.notes, None), [])

	def test_excerpt_like_the_web_app(self):
		text = "a" * 100 + " Ação importante " + "b" * 200
		ex = search.excerpt(text, "acao")
		self.assertTrue(ex.startswith("…") and ex.endswith("…"))
		self.assertIn("Ação", ex)
		self.assertLessEqual(len(ex), search.EXCERPT_LENGTH + 2)
		self.assertEqual(search.excerpt("curto", "zz"), "curto")
		self.assertEqual(search.excerpt("x" * 200, "zz"), "x" * 120 + "…")

	def test_fold_keeps_positions(self):
		folded, positions = search.foldWithMap("Straße é")
		self.assertEqual(folded, "strasse e")
		self.assertEqual(len(positions), len(folded))

	def test_limit(self):
		s = newStore()
		for i in range(150):
			s.addNote("nota %d" % i)
		self.assertEqual(len(search.search(s.notes, "nota")), search.MAX_RESULTS)


class FUN11_File(unittest.TestCase):
	def test_missing_file_is_empty(self):
		s = newStore()
		self.assertEqual((s.notes, s.notebooks, s.folders, s.warning), ([], [], [], None))
		self.assertFalse(os.path.exists(s.path))

	def test_save_and_load_everything(self):
		folder = _helpers.tempFolder()
		s = newStore(folder)
		f = s.addFolder("F")
		nb = s.addNotebook("N", f["id"])
		n = s.addNote("T", "done", nb["id"])
		again = newStore(folder)
		self.assertEqual((again.folders, again.notebooks, again.notes), ([f], [nb], [n]))
		with open(s.path, encoding="utf-8") as fh:
			data = json.load(fh)
		self.assertEqual((data["format"], data["version"]), ("notas-workflow", 1))

	def test_backup_and_no_temporary_file(self):
		s = newStore()
		s.addNote("a")
		s.addNote("b")
		self.assertTrue(os.path.exists(s.backupPath))
		with open(s.backupPath, encoding="utf-8") as fh:
			self.assertEqual(len(json.load(fh)["notes"]), 1)
		self.assertFalse(os.path.exists(s.path + ".tmp"))

	def test_damaged_file_is_kept_and_backup_used(self):
		folder = _helpers.tempFolder()
		s = newStore(folder)
		s.addNote("a")
		s.addNote("b")
		with open(s.path, "w", encoding="utf-8") as fh:
			fh.write("{ damaged")
		again = newStore(folder)
		self.assertEqual([n["title"] for n in again.notes], ["a"])
		self.assertEqual(again.warning[0], "corrupt")
		self.assertTrue(again.warning[2])
		kept = [f for f in os.listdir(folder) if ".corrupt-" in f]
		self.assertEqual(len(kept), 1)
		with open(os.path.join(folder, kept[0]), encoding="utf-8") as fh:
			self.assertEqual(fh.read(), "{ damaged")

	def test_damaged_without_backup(self):
		folder = _helpers.tempFolder()
		with open(os.path.join(folder, store.FILE_NAME), "w", encoding="utf-8") as fh:
			fh.write("[1, 2")
		s = newStore(folder)
		self.assertEqual((s.notes, s.warning[0], s.warning[2]), ([], "corrupt", False))

	def test_deeply_nested_file_is_treated_as_damaged(self):
		folder = _helpers.tempFolder()
		with open(os.path.join(folder, store.FILE_NAME), "w", encoding="utf-8") as fh:
			fh.write("[" * 100000 + "]" * 100000)
		s = newStore(folder)
		self.assertEqual((s.notes, s.warning[0]), ([], "corrupt"))

	def test_invalid_items_are_dropped(self):
		folder = _helpers.tempFolder()
		data = {"notes": [
			{"id": "ok-1", "title": "a", "laneId": "done"},
			{"id": "../../x", "title": "bad id"},
			{"title": "no id"},
			"text",
			{"id": "ok-1", "title": "duplicated"},
			{"id": "ok-2", "title": 5, "content": 7, "tags": "a,b", "laneId": "zzz", "notebookId": "ghost", "createdAt": "x"},
		]}
		with open(os.path.join(folder, store.FILE_NAME), "w", encoding="utf-8") as fh:
			json.dump(data, fh)
		s = newStore(folder)
		self.assertEqual([n["id"] for n in s.notes], ["ok-1", "ok-2"])
		n2 = s.notes[1]
		self.assertEqual((n2["title"], n2["content"], n2["tags"], n2["laneId"], n2["notebookId"]), ("", "", ["a", "b"], "todo", None))
		self.assertIsNotNone(model.parseIso(n2["createdAt"]))

	def test_write_error(self):
		folder = _helpers.tempFolder()
		blocker = os.path.join(folder, "file")
		open(blocker, "w").close()
		s = store.NotesStore(os.path.join(blocker, "sub"))
		s.load()
		with self.assertRaises(store.StoreError) as cm:
			s.addNote("a")
		self.assertEqual(cm.exception.kind, "write")
		self.assertEqual(len(s.notes), 1)

	def test_external_change_is_detected(self):
		folder = _helpers.tempFolder()
		s = newStore(folder)
		s.addNote("a")
		self.assertFalse(s.reloadIfChanged())
		other = newStore(folder)
		other.addNote("b")
		os.utime(s.path, ns=(1, 1))
		self.assertTrue(s.reloadIfChanged())
		self.assertEqual(len(s.notes), 2)

	def test_utf8_bom_accepted(self):
		folder = _helpers.tempFolder()
		with open(os.path.join(folder, store.FILE_NAME), "wb") as fh:
			fh.write(b"\xef\xbb\xbf" + json.dumps({"notes": [{"id": "a", "title": "é"}]}).encode("utf-8"))
		self.assertEqual(newStore(folder).notes[0]["title"], "é")


class FUN12_ImportExport(unittest.TestCase):
	def write(self, data, raw=None):
		path = os.path.join(_helpers.tempFolder(), "import.json")
		with open(path, "w", encoding="utf-8") as fh:
			fh.write(raw if raw is not None else json.dumps(data))
		return path

	def test_export_then_import_elsewhere(self):
		s = newStore()
		nb = s.addNotebook("N")
		s.addNote("a", notebookId=nb["id"])
		path = os.path.join(_helpers.tempFolder(), "out.json")
		s.exportFile(path)
		other = newStore()
		counts = other.importFile(path)
		self.assertEqual(counts, {"notes": 1, "notebooks": 1, "folders": 0})
		self.assertEqual(other.notes, s.notes)
		self.assertEqual(other.importFile(path), {"notes": 0, "notebooks": 0, "folders": 0})

	def test_web_formats(self):
		web = {"id": "w1", "title": "web", "content": "<p>x</p>", "tags": [], "laneId": "inprogress", "notebookId": None, "folderId": None, "createdAt": "2026-06-28T10:00:00.000Z", "updatedAt": "2026-06-28T10:00:00.000Z"}
		for data in ([web], {"notes": [web]}, {"notes": {"w1": web}}, {"notas-workflow:notes": json.dumps([web]), "notas-workflow:notebooks": "[]"}):
			s = newStore()
			self.assertEqual(s.importFile(self.write(data))["notes"], 1, data)
			self.assertEqual(s.notes[0]["laneId"], "inprogress")

	def test_newer_version_wins(self):
		s = newStore()
		n = s.addNote("local")
		older = dict(n, title="older", updatedAt="2000-01-01T00:00:00.000Z")
		newer = dict(n, title="newer", updatedAt="2999-01-01T00:00:00.000Z")
		s.importFile(self.write([older]))
		self.assertEqual(s.notes[0]["title"], "local")
		s.importFile(self.write([newer]))
		self.assertEqual(s.notes[0]["title"], "newer")

	def test_invalid_files(self):
		s = newStore()
		for raw in ("not json", "42", '{"x": 1}', '"text"'):
			with self.assertRaises(store.StoreError) as cm:
				s.importFile(self.write(None, raw))
			self.assertEqual(cm.exception.kind, "invalidImport", raw)
		with self.assertRaises(store.StoreError):
			s.importFile(os.path.join(_helpers.tempFolder(), "missing.json"))

	def test_export_error(self):
		s = newStore()
		with self.assertRaises(store.StoreError):
			s.exportFile(os.path.join(_helpers.tempFolder(), "missing", "dir", "x.json"))


class FUN13_Relocate(unittest.TestCase):
	def test_copy_to_empty_folder(self):
		s = newStore()
		s.addNote("a")
		target = _helpers.tempFolder()
		self.assertEqual(s.relocate(target), "copied")
		self.assertEqual(newStore(target).notes[0]["title"], "a")

	def test_use_notes_of_the_new_folder(self):
		target = _helpers.tempFolder()
		newStore(target).addNote("there")
		s = newStore()
		s.addNote("here")
		self.assertEqual(s.relocate(target), "loaded")
		self.assertEqual([n["title"] for n in s.notes], ["there"])

	def test_failed_copy_keeps_the_old_folder(self):
		s = newStore()
		old = s.folder
		blocker = os.path.join(_helpers.tempFolder(), "file")
		open(blocker, "w").close()
		with self.assertRaises(store.StoreError):
			s.relocate(os.path.join(blocker, "x"))
		self.assertEqual(s.folder, old)


class FUN21_MoveToNotebookOrFolder(unittest.TestCase):
	"""1.2.0: Move to puts a note in a notebook, directly in a folder or makes it loose."""

	def setUp(self):
		s = self.s = newStore()
		self.folder = s.addFolder("Projetos")
		self.nb = s.addNotebook("Site", self.folder["id"])
		self.note = s.addNote("a")

	def test_notebook_folder_and_loose(self):
		s, n = self.s, self.note
		self.assertTrue(s.moveNoteTo(n["id"], notebookId=self.nb["id"]))
		self.assertEqual((n["notebookId"], n["folderId"]), (self.nb["id"], None))
		self.assertTrue(s.moveNoteTo(n["id"], folderId=self.folder["id"]))
		self.assertEqual((n["notebookId"], n["folderId"]), (None, self.folder["id"]))
		self.assertTrue(s.moveNoteTo(n["id"]))
		self.assertEqual((n["notebookId"], n["folderId"]), (None, None))
		self.assertFalse(s.moveNoteTo(n["id"]))

	def test_notebook_wins_and_unknown_places_become_loose(self):
		s, n = self.s, self.note
		s.moveNoteTo(n["id"], notebookId=self.nb["id"], folderId=self.folder["id"])
		self.assertEqual((n["notebookId"], n["folderId"]), (self.nb["id"], None))
		s.moveNoteTo(n["id"], notebookId="ghost", folderId="ghost")
		self.assertEqual((n["notebookId"], n["folderId"]), (None, None))

	def test_branches(self):
		s = self.s
		direct = s.addNote("b", folderId=self.folder["id"])
		inNb = s.addNote("c", notebookId=self.nb["id"])
		self.assertEqual(s.notesInFolder(self.folder["id"]), [direct])
		self.assertEqual(s.notesIn(self.nb["id"]), [inNb])
		self.assertEqual(s.looseNotes(), [self.note])

	def test_saved_and_read_again(self):
		self.s.moveNoteTo(self.note["id"], folderId=self.folder["id"])
		again = newStore(self.s.folder)
		self.assertEqual(again.getNote(self.note["id"])["folderId"], self.folder["id"])


class FUN22_Performance(unittest.TestCase):
	"""1.2.0: index by id and prepared search text."""

	def test_get_note_uses_the_index_and_follows_changes(self):
		s = newStore()
		notes = [s.addNote("n%d" % i) for i in range(50)]
		self.assertIs(s.getNote(notes[30]["id"]), notes[30])
		s.deleteNote(notes[30]["id"])
		self.assertIsNone(s.getNote(notes[30]["id"]))
		s.notes = notes[:10]
		self.assertIsNone(s.getNote(notes[40]["id"]))
		self.assertIs(s.getNote(notes[5]["id"]), notes[5])

	def test_import_replacing_a_note_updates_the_index(self):
		s = newStore()
		n = s.addNote("velha")
		path = os.path.join(_helpers.tempFolder(), "x.json")
		with open(path, "w", encoding="utf-8") as fh:
			json.dump([dict(n, title="nova", updatedAt="2999-01-01T00:00:00.000Z")], fh)
		s.importFile(path)
		self.assertEqual(s.getNote(n["id"])["title"], "nova")

	def test_index_reuses_and_rebuilds_entries(self):
		s = newStore()
		n = s.addNote("Reunião")
		index = search.SearchIndex()
		first = index.entry(n)
		self.assertIs(index.entry(n), first)
		s.updateNote(n["id"], content="<p>orçamento</p>")
		self.assertIsNot(index.entry(n), first)
		self.assertEqual([x["id"] for x, _s, _e in search.search(s.notes, "orcamento", index=index)], [n["id"]])
		s.updateNote(n["id"], tags=["urgente"])
		self.assertEqual(len(search.search(s.notes, "urgente", index=index)), 1)
		index.forget(set())
		self.assertEqual(len(index), 0)

	def test_fast_plain_text_drops_tags_scripts_and_styles(self):
		self.assertEqual(search.plainText("<p>a <b>b</b></p><script>x()</script><style>p{}</style><p>&amp; c</p>"), "a b & c")
		self.assertEqual(search.fold("Ação Straße ÉÏ"), "acao strasse ei")

	def test_file_is_compact(self):
		s = newStore()
		s.addNote("a")
		with open(s.path, encoding="utf-8") as fh:
			self.assertNotIn("\n", fh.read())

	def test_limit_is_200_mb(self):
		self.assertEqual(store.MAX_FILE_SIZE, 200 * 1024 * 1024)


class FUN20_LegacyName(unittest.TestCase):
	"""1.1.0: the add-on was renamed from NotasWorkflow to NotasWorkflowNVDA."""

	def legacyFolder(self, title="antiga"):
		folder = _helpers.tempFolder()
		with open(os.path.join(folder, store.LEGACY_FILE_NAME), "w", encoding="utf-8") as fh:
			json.dump({"format": "notas-workflow", "version": 1, "notes": [{"id": "a1", "title": title}]}, fh)
		return folder

	def test_old_file_of_the_folder_is_copied_to_the_new_name(self):
		folder = self.legacyFolder()
		s = newStore(folder)
		self.assertTrue(s.migrated)
		self.assertEqual([n["title"] for n in s.notes], ["antiga"])
		self.assertTrue(os.path.isfile(os.path.join(folder, store.FILE_NAME)))

	def test_old_file_is_never_changed_or_deleted(self):
		folder = self.legacyFolder()
		legacy = os.path.join(folder, store.LEGACY_FILE_NAME)
		with open(legacy, "rb") as fh:
			before = fh.read()
		s = newStore(folder)
		s.addNote("nova")
		with open(legacy, "rb") as fh:
			self.assertEqual(fh.read(), before)

	def test_new_file_wins_and_copy_happens_once(self):
		folder = self.legacyFolder()
		newStore(folder).addNote("depois")
		again = newStore(folder)
		self.assertFalse(again.migrated)
		self.assertEqual([n["title"] for n in again.notes], ["antiga", "depois"])

	def test_names(self):
		self.assertEqual((store.FILE_NAME, store.LEGACY_FILE_NAME), ("NotasWorkflowNVDA-data.json", "NotasWorkflow-data.json"))
		self.assertEqual(store.FORMAT, "notas-workflow")


class FUN19_Dates(unittest.TestCase):
	def test_iso_like_javascript(self):
		dt = datetime.datetime(2026, 10, 12, 18, 41, 5, 123456, tzinfo=datetime.timezone.utc)
		self.assertEqual(model.nowIso(dt), "2026-10-12T18:41:05.123Z")
		self.assertRegex(model.nowIso(), r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$")

	def test_parse(self):
		self.assertEqual(model.parseIso("2026-10-12T18:41:05.123Z").year, 2026)
		self.assertIsNotNone(model.parseIso("2026-10-12T18:41:05+03:00"))
		for bad in (None, 5, "", "ontem", "x" * 100):
			self.assertIsNone(model.parseIso(bad))


class FUN27_Export(unittest.TestCase):
	"""Export as Word, Markdown and HTML (exporter.py, 1.4.0)."""

	CONTENT = markup.textToHtml(
		"Intro **negrito** e *itálico* ~~riscado~~ `cod`\n# Grande\n## Seção\n### Sub\n- a\n- b\n3. três\n4. quatro\n"
		"> citação\n```\nx = 1 < 2\n```\n---"
	)

	def notes(self):
		return [
			{"id": "a", "title": "Nota *A* & <b>", "content": self.CONTENT, "tags": ["t"], "laneId": "todo"},
			{"id": "b", "title": "", "content": "<p>texto</p>", "tags": [], "laneId": "done"},
		]

	def document(self, title="Caderno X"):
		return exporter.buildDocument(title, "Exportado: 2 folhas", [(None, self.notes())], lambda n: ["Status: A fazer"], lambda n: n["title"] or "Sem título")

	def test_document_structure(self):
		blocks = self.document()
		headings = [(b["level"], b["runs"][0][0]) for b in blocks if b["kind"] == "h"]
		self.assertEqual(headings[:2], [(1, "Caderno X"), (2, "Nota *A* & <b>")])
		# Headings of the content stay below the note: # and ## -> 3, ### -> 4.
		self.assertEqual(headings[2:5], [(3, "Grande"), (3, "Seção"), (4, "Sub")])
		self.assertEqual(headings[-1], (2, "Sem título"))
		self.assertTrue(any(b["kind"] == "p" and b.get("meta") for b in blocks))

	def test_single_note_is_heading_1(self):
		blocks = exporter.buildDocument(None, None, [(None, self.notes()[:1])], lambda n: [], lambda n: n["title"])
		self.assertEqual((blocks[0]["kind"], blocks[0]["level"]), ("h", 1))
		self.assertEqual([b["level"] for b in blocks if b["kind"] == "h"][1:4], [2, 2, 3])

	def test_folder_sections(self):
		blocks = exporter.buildDocument("Pasta P", None, [("Direto", []), ("Caderno C", self.notes()[1:])], lambda n: [], lambda n: "N")
		self.assertEqual([(b["level"], b["runs"][0][0]) for b in blocks if b["kind"] == "h"], [(1, "Pasta P"), (2, "Caderno C"), (3, "N")])

	def test_markdown(self):
		md = exporter.toMarkdown(self.document())
		for expected in (
			"# Caderno X\n", "## Nota \\*A\\* & \\<b\\>\n", "Intro **negrito** e *itálico* ~~riscado~~ `cod`\n",
			"### Grande", "#### Sub", "- a\n- b\n", "3. três\n4. quatro\n", "> citação\n", "```\nx = 1 < 2\n```\n", "---\n",
			"Status: A fazer",
		):
			self.assertIn(expected, md)
		self.assertNotIn("\n\n\n", md)
		# Lines that would become a list, a heading or a quote in Markdown are escaped.
		meta = exporter.toMarkdown(exporter.buildDocument(None, None, [(None, self.notes()[1:])], lambda n: ["1. um", "# dois", "- três", "> quatro"], lambda n: "T"))
		self.assertIn("\n1\\. um\n\n\\# dois\n\n\\- três\n\n\\> quatro\n", meta)

	def test_html(self):
		page = exporter.toHtml(self.document(), "Caderno <X>", "pt-BR")
		self.assertTrue(page.startswith('<!DOCTYPE html>\n<html lang="pt-BR">'))
		self.assertIn("<title>Caderno &lt;X&gt;</title>", page)
		self.assertIn("<h2>Nota *A* &amp; &lt;b&gt;</h2>", page)
		self.assertIn('<p class="meta">Status: A fazer</p>', page)
		self.assertIn("<ul>\n<li>a</li>\n<li>b</li>\n</ul>", page)
		self.assertIn('<ol start="3">', page)
		self.assertIn("<blockquote>\n<p>citação</p>\n</blockquote>", page)
		self.assertIn("<pre><code>x = 1 &lt; 2</code></pre>", page)
		self.assertIn("<strong>negrito</strong>", page)
		self.assertIn("<h3>Grande</h3>", page)

	def test_docx(self):
		import zipfile
		from xml.dom import minidom

		path = os.path.join(_helpers.tempFolder(), "x.docx")
		exporter.writeDocx(path, self.document(), "Caderno X", "pt-BR")
		with zipfile.ZipFile(path) as z:
			parts = {name: z.read(name).decode("utf-8") for name in z.namelist()}
		for xml in parts.values():
			minidom.parseString(xml.encode("utf-8"))
		doc = parts["word/document.xml"]
		self.assertIn('<w:pStyle w:val="Heading1"/>', doc)
		self.assertIn('<w:pStyle w:val="Heading4"/>', doc)
		self.assertIn("Nota *A* &amp; &lt;b&gt;", doc)
		self.assertIn("<w:b/>", doc)
		self.assertIn("<w:strike/>", doc)
		self.assertIn('<w:numId w:val="1"/>', doc)
		self.assertIn('<w:startOverride w:val="3"/>', parts["word/numbering.xml"])
		self.assertIn('w:outlineLvl w:val="0"', parts["word/styles.xml"])
		self.assertIn('w:lang w:val="pt-BR"', parts["word/styles.xml"])
		self.assertIn("<dc:title>Caderno X</dc:title>", parts["docProps/core.xml"])
		# Same notes, same file.
		again = os.path.join(_helpers.tempFolder(), "x.docx")
		exporter.writeDocx(again, self.document(), "Caderno X", "pt-BR")
		with open(path, "rb") as f1, open(again, "rb") as f2:
			self.assertEqual(f1.read(), f2.read())

	def test_ordered_lists_restart(self):
		content = markup.textToHtml("1. um\n2. dois\n\n1. outro")
		blocks = exporter.contentBlocks(content)
		self.assertEqual([(b["number"], b["list"]) for b in blocks if b["kind"] == "li"], [(1, 1), (2, 1), (1, 2)])

	def test_characters_that_cannot_be_written(self):
		note = {"id": "x", "title": "a\x01b\ud800c", "content": "<p>d\x0be</p>", "tags": [], "laneId": "todo"}
		blocks = exporter.buildDocument(None, None, [(None, [note])], lambda n: [], lambda n: n["title"])
		folder = _helpers.tempFolder()
		for fmt in exporter.FORMATS:
			path = os.path.join(folder, "x" + exporter.EXTENSIONS[fmt])
			exporter.writeDocument(path, fmt, blocks, note["title"], "en")
			self.assertTrue(os.path.getsize(path) > 0)
		self.assertEqual(exporter.toMarkdown(blocks), "# abc\n\nde\n")

	def test_empty_content(self):
		blocks = exporter.buildDocument(None, None, [(None, [{"id": "x", "title": "T", "content": "", "tags": [], "laneId": "todo"}])], lambda n: [], lambda n: "T")
		self.assertEqual(len(blocks), 1)
		path = os.path.join(_helpers.tempFolder(), "x.docx")
		exporter.writeDocx(path, [], "T", "en")
		self.assertTrue(os.path.isfile(path))

	def test_safe_names(self):
		self.assertEqual(exporter.safeName('a<b>:"c/d\\e|f?g*h', "x"), "abcdefgh")
		self.assertEqual(exporter.safeName("CON", "x"), "_CON")
		self.assertEqual(exporter.safeName("com1.txt", "x"), "_com1.txt")
		self.assertEqual(exporter.safeName(" ... ", "Sem título"), "Sem título")
		self.assertEqual(exporter.safeName("..\\..\\fora", "x"), "....fora")
		self.assertEqual(len(exporter.safeName("x" * 500, "y")), exporter.MAX_NAME)

	def test_one_file_for_each_note_never_overwrites(self):
		folder = _helpers.tempFolder()
		with open(os.path.join(folder, "Caderno"), "w") as f:
			f.write("já existe")
		same = [{"id": "1", "title": "Igual", "content": "", "tags": [], "laneId": "todo"}, {"id": "2", "title": "igual", "content": "", "tags": [], "laneId": "todo"}]
		root, count = exporter.writeSeparate(
			folder, "Caderno", "md", [(None, same), ("Sub", same[:1]), ("sub", same[:1])],
			lambda n: exporter.buildDocument(None, None, [(None, [n])], lambda x: [], lambda x: x["title"]),
			lambda n: n["title"], "en", "Sem título",
		)
		self.assertEqual((os.path.basename(root), count), ("Caderno (2)", 4))
		self.assertEqual(sorted(os.listdir(root)), ["Igual.md", "Sub", "igual (2).md", "sub (2)"])
		with open(os.path.join(folder, "Caderno")) as f:
			self.assertEqual(f.read(), "já existe")


class FUN16_Compiles(unittest.TestCase):
	def test_every_file_compiles_on_this_python(self):
		out = _helpers.tempFolder()
		for folder, _dirs, files in os.walk(os.path.join(_helpers.ROOT, "addon")):
			for name in files:
				if name.endswith(".py"):
					py_compile.compile(os.path.join(folder, name), doraise=True, cfile=os.path.join(out, name + "c"))


if __name__ == "__main__":
	unittest.main()
