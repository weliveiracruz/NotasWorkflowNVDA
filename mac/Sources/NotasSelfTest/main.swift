// Notas Workflow Mac - NotasSelfTest
// Tests of NotasCore, the same cases of tests/test_pure.py of NotasWorkflowNVDA.
// Run with: swift run NotasSelfTest   (exit code 0 when everything passes)
// Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
// This file is covered by the GNU General Public License, version 2.

import Foundation
import NotasCore

// NotasSelfTest --regravar <pasta>: reads the notes of the folder and writes them again
// (used to check that the NVDA add-on and this app read each other's file).
if CommandLine.arguments.count == 3 && CommandLine.arguments[1] == "--regravar" {
	let store = NotesStore(folder: CommandLine.arguments[2])
	store.load()
	do {
		try store.save()
		print("\(store.notes.count) folhas regravadas")
		exit(0)
	} catch {
		print("erro: \(error)")
		exit(1)
	}
}

// NotasSelfTest --markup <file.json>: converts each text of a JSON list with textToHtml,
// htmlToText and plainText (used to compare with markup.py of the NVDA add-on).
if CommandLine.arguments.count == 3 && CommandLine.arguments[1] == "--markup" {
	let data = try! Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[2]))
	let texts = try! JSONSerialization.jsonObject(with: data) as! [String]
	let out = texts.map { t -> [String] in
		let html = Markup.textToHtml(t)
		return [html, Markup.htmlToText(html), Markup.plainText(html), Markup.htmlToText(t), Search.plainText(t)]
	}
	FileHandle.standardOutput.write(try! JSONSerialization.data(withJSONObject: out))
	exit(0)
}

var passed = 0
var failed: [String] = []

func check(_ condition: @autoclosure () -> Bool, _ name: String, file: String = #fileID, line: Int = #line) {
	if condition() {
		passed += 1
	} else {
		failed.append("\(name) (line \(line))")
		print("FALHOU: \(name) (linha \(line))")
	}
}

func equal<T: Equatable>(_ a: T, _ b: T, _ name: String, line: Int = #line) {
	if a == b {
		passed += 1
	} else {
		failed.append("\(name) (line \(line))")
		print("FALHOU: \(name) (linha \(line))\n  obtido:   \(a)\n  esperado: \(b)")
	}
}

func tempFolder() -> String {
	let path = (NSTemporaryDirectory() as NSString).appendingPathComponent("NotasSelfTest-\(UUID().uuidString)")
	try! FileManager.default.createDirectory(atPath: path, withIntermediateDirectories: true)
	return path
}

func newStore(_ folder: String? = nil) -> NotesStore {
	let s = NotesStore(folder: folder ?? tempFolder())
	s.load()
	return s
}

func fmt(_ r: (String, Int, Int, Bool)) -> String {
	"\(r.0)|\(r.1)|\(r.2)|\(r.3)"
}

// MARK: notes

do {
	let s = newStore()
	let n = try s.addNote(title: "  Título\nnovo  ")
	equal(n.title, "Título novo", "title is single line and trimmed")
	equal(n.laneId, "todo", "default lane")
	check(n.createdAt == n.updatedAt, "createdAt equals updatedAt")
	check(Model.isValidId(n.id) && n.id.count == 36, "ids are uuid4")
	try equal(s.updateNote(n.id, NotePatch(title: "Título novo")), false, "no change keeps updatedAt")
	try equal(s.updateNote(n.id, NotePatch(tags: ["a", "A", " b ", ""])), true, "tags change")
	equal(s.getNote(n.id)!.tags, ["a", "b"], "tags are cleaned")
	equal(Model.cleanTags(Array(repeating: 0, count: 40).enumerated().map { "t\($0.offset)" }).count, 30, "tags limit")
	let ghost = try s.addNote(title: "x", laneId: "nope", notebookId: "ghost")
	equal(ghost.laneId, "todo", "unknown lane refused")
	check(ghost.notebookId == nil, "unknown notebook refused")
	do {
		try s.deleteNote("missing")
		check(false, "missing note raises")
	} catch let e as StoreError {
		equal(e.kind, .notFound, "missing note raises notFound")
	}
	try s.updateNote(n.id, NotePatch(title: "b", content: "<p>c</p>"))
	s.flush()
	let again = newStore(s.folder)
	equal(again.getNote(n.id)?.content, "<p>c</p>", "change is saved to the file")
} catch {
	check(false, "notes: \(error)")
}

// MARK: formatting

equal(fmt(Markup.applyFormat("ola mundo", 4, 9, "bold")), "ola **mundo**|6|11|true", "bold wraps")
equal(fmt(Markup.applyFormat("ola **mundo**", 6, 11, "bold")), "ola mundo|4|9|false", "bold unwraps")
equal(fmt(Markup.applyFormat("ola **mundo**", 4, 13, "bold")), "ola mundo|4|9|false", "bold unwraps selection with marks")
equal(fmt(Markup.applyFormat("ab", 1, 1, "italic")), "a**b|2|2|true", "empty selection")
for (kind, mark) in [("italic", "*"), ("strike", "~~"), ("code", "`")] {
	equal(Markup.applyFormat("x y", 2, 3, kind).0, "x \(mark)y\(mark)", "inline mark \(kind)")
}
equal(Markup.applyFormat("a\nb\nc", 2, 2, "heading2").0, "a\n## b\nc", "heading2")
equal(Markup.applyFormat("a\n## b", 3, 3, "heading3").0, "a\n### b", "heading3 replaces heading2")
equal(Markup.applyFormat("a\nb", 0, 3, "bullet").0, "- a\n- b", "bullet")
equal(Markup.applyFormat("- a\n- b", 0, 7, "bullet").0, "a\nb", "bullet removed")
equal(Markup.applyFormat("a\nb\nc", 0, 5, "ordered").0, "1. a\n2. b\n3. c", "ordered")
equal(Markup.applyFormat("a", 0, 0, "quote").0, "> a", "quote")
equal(Markup.applyFormat("> a", 0, 0, "quote").0, "a", "quote removed")
equal(Markup.applyFormat("ab", 1, 1, "divider").0, "a\n---\nb", "divider")
equal(Markup.applyFormat("", 0, 0, "divider").0, "---\n", "divider in empty text")
equal(Markup.applyFormat("ab", 5, -3, "bold").0, "**ab**", "out of range selection")
equal(Markup.formats, ["bold", "italic", "strike", "code", "heading2", "heading3", "bullet", "ordered", "quote", "divider"], "formats of the web toolbar")

// MARK: markup and HTML

let sample = "# Título\n\nlinha **negrito** e *itálico* 2*3*4 <script>\n- a\n- b\n3. x\n4. y\n> citação\n> \n---\n```\ncódigo <b>\n```\n~~riscado~~ `c*d*`"
equal(Markup.htmlToText(Markup.textToHtml(sample)), sample, "round trip without loss")
equal(Markup.textToHtml("## T\n- a\n1. b\n> q\n---\n**x** *y* ~~z~~ `w`"),
	"<h2>T</h2><ul><li><p>a</p></li></ul><ol><li><p>b</p></li></ol><blockquote><p>q</p></blockquote><hr><p><strong>x</strong> <em>y</em> <s>z</s> <code>w</code></p>", "TipTap HTML")
equal(Markup.textToHtml("a\n\nb"), "<p>a</p><p></p><p>b</p>", "blank lines are empty paragraphs")
let escaped = Markup.textToHtml("<img src=x onerror=alert(1)> & \"x\"")
check(!escaped.contains("<img") && escaped.contains("&lt;img") && escaped.contains("&amp;"), "text is escaped")
equal(Markup.htmlToText("<h3>Pauta</h3><p>Olá <b>mundo</b> <i>x</i><br>linha 2</p><ul><li><p>um</p><ul><li><p>sub</p></li></ul></li></ul><ol start=\"5\"><li><p>cinco</p></li></ol><pre><code>a\nb</code></pre>"),
	"### Pauta\nOlá **mundo** *x*\nlinha 2\n- um\n  - sub\n5. cinco\n```\na\nb\n```", "HTML of the web editor")
let unknown = "<p>a<script>alert(1)</script><style>p{}</style><span class=x onclick=y>b</span><custom>c</custom></p>"
equal(Markup.htmlToText(unknown), "abc", "script, style and unknown tags")
equal(Markup.plainText(unknown), "abc", "plain text drops script")
equal(Markup.htmlToText("<p>&lt;x&gt; &amp; &eacute; &#233;</p>"), "<x> & é é", "entities")
equal(Markup.htmlToText("só texto &amp; mais\nlinha"), "só texto & mais\nlinha", "plain text content")
let previewHtml = Markup.textToHtml("## Título\n- **item** um\n\n" + String(repeating: "palavra ", count: 50))
equal(Array(Markup.plainText(previewHtml).components(separatedBy: "\n").prefix(2)), ["Título", "item um"], "plain text lines")
equal(Markup.preview(previewHtml).count, 100, "preview has 100 characters")
for broken in ["<p>a", "</p></ul></blockquote>b", "<ol start='99999999999999'><li>x</li></ol>", "<<<>>>", String(repeating: "<p", count: 1000)] {
	_ = Markup.htmlToText(broken)
}
check(true, "broken HTML does not crash")

// MARK: lanes and filters

equal(Model.laneIds, ["todo", "inprogress", "blocked", "done"], "lanes of the web app")
equal(Model.neighbourLane("todo", 1), "inprogress", "next lane")
equal(Model.neighbourLane("done", -1), "blocked", "previous lane")
check(Model.neighbourLane("todo", -1) == nil && Model.neighbourLane("done", 1) == nil, "no lane beyond the ends")

do {
	let s = newStore()
	let a = try s.addNote(title: "a")
	let b = try s.addNote(title: "b", laneId: "done")
	let c = try s.addNote(title: "c")
	let lanes = Model.byLane(s.notes)
	equal(lanes["todo"]!.map(\.id), [a.id, c.id], "byLane keeps the order")
	equal(lanes["done"]!.map(\.id), [b.id], "byLane done")
	try equal(s.moveNote(a.id, laneId: "inprogress"), true, "move")
	try equal(s.moveNote(a.id, laneId: "inprogress"), false, "move to the same lane")
	try equal(s.moveNote(a.id, laneId: "nope"), false, "move to an unknown lane")

	let f = try s.addFolder("Projetos")
	let nbIn = try s.addNotebook("Dentro", folderId: f.id)
	let nbOut = try s.addNotebook("Fora")
	let s2 = newStore()
	let f2 = try s2.addFolder("Projetos")
	let in2 = try s2.addNotebook("Dentro", folderId: f2.id)
	let out2 = try s2.addNotebook("Fora")
	let loose = try s2.addNote(title: "solta")
	let inside = try s2.addNote(title: "dentro", notebookId: in2.id)
	let outside = try s2.addNote(title: "fora", notebookId: out2.id)
	let direct = try s2.addNote(title: "pasta direta", folderId: f2.id)
	equal(s2.filtered(.all).count, 4, "all")
	equal(s2.filtered(.loose).map(\.id), [loose.id], "loose")
	equal(s2.filtered(.notebook(out2.id)).map(\.id), [outside.id], "notebook")
	equal(s2.filtered(.folder(f2.id)).map(\.id), [inside.id, direct.id], "folder")
	_ = (nbIn, nbOut)
} catch {
	check(false, "lanes: \(error)")
}

do {
	let folder = tempFolder()
	var notes: [[String: Any]] = []
	for i in 0..<15 {
		notes.append(["id": "n\(i)", "title": "n\(i)", "laneId": "todo", "updatedAt": String(format: "2026-01-%02dT00:00:00.000Z", i + 1), "createdAt": "2026-01-01T00:00:00.000Z"])
	}
	let data = try JSONSerialization.data(withJSONObject: ["notes": notes])
	try data.write(to: URL(fileURLWithPath: (folder as NSString).appendingPathComponent(NotesStore.fileName)))
	let s = newStore(folder)
	equal(s.filtered(.recent).map(\.title), (5...14).reversed().map { "n\($0)" }, "recent are the 10 changed last")
} catch {
	check(false, "recent: \(error)")
}

// MARK: notebooks and folders

do {
	let s = newStore()
	let colors = try (0..<7).map { try s.addNotebook("n\($0)").color }
	equal(colors, Model.notebookColors + [Model.notebookColors[0]], "notebook colours rotate")
	try equal(s.addFolder("f").color, Model.folderColors[0], "folder colour")
	let nb = try s.addNotebook("x")
	let n = try s.addNote(title: "a", notebookId: nb.id)
	try s.deleteNotebook(nb.id)
	check(s.getNote(n.id) != nil && s.getNote(n.id)!.notebookId == nil, "deleting a notebook keeps its notes")
	let f = try s.addFolder("g")
	let nb2 = try s.addNotebook("y", folderId: f.id)
	let n2 = try s.addNote(title: "b", folderId: f.id)
	try s.deleteFolder(f.id)
	check(s.getNotebook(nb2.id)?.folderId == nil && s.getNote(n2.id)?.folderId == nil, "deleting a folder keeps notebooks and notes")
	try s.renameNotebook(nb2.id, "  z ")
	equal(s.getNotebook(nb2.id)?.name, "z", "rename trims")
	for call in [{ _ = try s.addNotebook("  ") }, { _ = try s.addFolder("") }, { try s.renameNotebook(nb2.id, "\n") }] as [() throws -> Void] {
		do {
			try call()
			check(false, "empty name refused")
		} catch let e as StoreError {
			equal(e.kind, .emptyName, "empty name refused")
		}
	}
	let ghostNotebook = try s.addNotebook("w", folderId: "ghost")
	check(ghostNotebook.folderId == nil, "notebook in unknown folder is loose")
} catch {
	check(false, "notebooks: \(error)")
}

// MARK: search

do {
	let s = newStore()
	let a = try s.addNote(title: "Reunião de ação")
	try s.updateNote(a.id, NotePatch(content: Markup.textToHtml("Pauta: **orçamento** do projeto"), tags: ["Trabalho"]))
	let b = try s.addNote(title: "Lista de compras")
	try s.updateNote(b.id, NotePatch(content: Markup.textToHtml("pão, café, reunião às 10h")))
	equal(Search.search(s.notes, "ACAO").map(\.note.id), [a.id], "ignores accents and case")
	equal(Search.search(s.notes, "orcamento").map(\.note.id), [a.id], "content is searched")
	let scores = Dictionary(uniqueKeysWithValues: Search.search(s.notes, "reuniao cafe").map { ($0.note.id, $0.score) })
	check(scores[a.id] == 0.5 && scores[b.id] == 1.0, "score is terms found over terms")
	equal(Search.search(s.notes, "reuniao").first?.note.id, a.id, "title breaks ties")
	equal(Search.search(s.notes, "trabalho").count, 1, "tags are searched")
	check(Search.search(s.notes, "strong").isEmpty && Search.search(s.notes, "**").isEmpty, "markup is not searched")
	check(Search.search(s.notes, "   ").isEmpty, "empty query")
	let text = String(repeating: "a", count: 100) + " Ação importante " + String(repeating: "b", count: 200)
	let ex = Search.excerpt(text, "acao")
	check(ex.hasPrefix("…") && ex.hasSuffix("…") && ex.contains("Ação") && ex.count <= Search.excerptLength + 2, "excerpt like the web app")
	equal(Search.excerpt("curto", "zz"), "curto", "short excerpt")
	equal(Search.excerpt(String(repeating: "x", count: 200), "zz"), String(repeating: "x", count: 120) + "…", "long excerpt without term")
	let many = newStore()
	for i in 0..<150 {
		_ = try many.addNote(title: "nota \(i)")
	}
	equal(Search.search(many.notes, "nota").count, Search.maxResults, "results limit")
} catch {
	check(false, "search: \(error)")
}

// MARK: file

do {
	let folder = tempFolder()
	let s = newStore(folder)
	check(s.notes.isEmpty && s.warning == nil, "missing file is empty")
	let f = try s.addFolder("F")
	let nb = try s.addNotebook("N", folderId: f.id)
	let n = try s.addNote(title: "a", laneId: "blocked", notebookId: nb.id)
	try s.updateNote(n.id, NotePatch(content: "<p>x</p>", tags: ["t"]))
	_ = try s.addNote(title: "b")
	let again = newStore(folder)
	equal(again.folders, s.folders, "folders saved")
	equal(again.notebooks, s.notebooks, "notebooks saved")
	equal(again.notes, s.notes, "notes saved")
	let fm = FileManager.default
	check(fm.fileExists(atPath: s.backupPath) && !fm.fileExists(atPath: s.path + ".tmp"), "backup and no temporary file")
	let text = try String(contentsOfFile: s.path, encoding: .utf8)
	check(text.hasPrefix("{\"format\":\"notas-workflow\",\"version\":1,\"folders\":[") && !text.contains("\n"), "file is compact, same shape of the add-on")

	// Damaged file: kept with another name and the backup is used.
	try "{broken".write(toFile: s.path, atomically: true, encoding: .utf8)
	let damaged = newStore(folder)
	if case let .corrupt(savedAs, restored)? = damaged.warning {
		check(restored && savedAs.hasPrefix("NotasWorkflowNVDA-data.corrupt-"), "damaged file kept and backup used")
	} else {
		check(false, "damaged file gives a warning")
	}
	check(!damaged.notes.isEmpty, "backup notes used")

	// BOM, web formats and import.
	let other = tempFolder()
	let bomPath = (other as NSString).appendingPathComponent("web.json")
	let web: [String: Any] = ["notas-workflow:notes": "[{\"id\":\"w1\",\"title\":\"web\",\"laneId\":\"done\",\"updatedAt\":\"2026-02-01T10:00:00.000Z\"}]"]
	var bytes = Data([0xEF, 0xBB, 0xBF])
	bytes.append(try JSONSerialization.data(withJSONObject: web))
	try bytes.write(to: URL(fileURLWithPath: bomPath))
	let counts = try again.importFile(bomPath)
	equal(counts.notes, 1, "import of the web format with BOM")
	equal(again.getNote("w1")?.laneId, "done", "imported note")
	try equal(again.importFile(bomPath).notes, 0, "same note is not imported twice")
	let junk = (other as NSString).appendingPathComponent("junk.json")
	try "{\"x\":1}".write(toFile: junk, atomically: true, encoding: .utf8)
	do {
		_ = try again.importFile(junk)
		check(false, "invalid import refused")
	} catch let e as StoreError {
		equal(e.kind, .invalidImport, "invalid import refused")
	}
	let exportPath = (other as NSString).appendingPathComponent("export.json")
	try again.exportFile(exportPath)
	let fresh = newStore(tempFolder())
	try equal(fresh.importFile(exportPath).notes, again.notes.count, "export then import elsewhere")

	// Another folder: copy when empty, its notes when it has them.
	let empty = tempFolder()
	let moved = newStore(folder)
	let firstMove = try moved.relocate(empty)
	check(firstMove == .copied, "copy to an empty folder")
	check(fm.fileExists(atPath: (empty as NSString).appendingPathComponent(NotesStore.fileName)), "file copied")
	let secondMove = try moved.relocate(other)
	let thirdMove = try moved.relocate(empty)
	check(secondMove == .copied && thirdMove == .loaded, "notes of the new folder are used")

	// External change detected.
	let watched = newStore(folder)
	check(!watched.changedOnDisk(), "own file is not a change")
	Thread.sleep(forTimeInterval: 1.1)
	try "{\"notes\":[]}".write(toFile: watched.path, atomically: true, encoding: .utf8)
	check(watched.reloadIfChanged() && watched.notes.isEmpty, "external change is detected")

	// Old file of the folder copied to the new name, never changed.
	let legacyFolder = tempFolder()
	let legacyPath = (legacyFolder as NSString).appendingPathComponent(NotesStore.legacyFileName)
	try "{\"notes\":[{\"id\":\"old\",\"title\":\"velha\"}]}".write(toFile: legacyPath, atomically: true, encoding: .utf8)
	let legacy = newStore(legacyFolder)
	check(legacy.migrated && legacy.getNote("old") != nil && fm.fileExists(atPath: legacyPath), "old file copied to the new name")
} catch {
	check(false, "file: \(error)")
}

// MARK: background saving and dates

do {
	let folder = tempFolder()
	let s = newStore(folder)
	s.enableBackgroundSaving()
	for i in 0..<50 {
		_ = try s.addNote(title: "n\(i)")
	}
	check(s.flush() == nil, "background write without error")
	equal(newStore(folder).notes.count, 50, "everything written after flush")
} catch {
	check(false, "background: \(error)")
}

let iso = Model.nowIso(Date(timeIntervalSince1970: 1_760_000_000.5))
equal(iso, "2025-10-09T08:53:20.500Z", "ISO like JavaScript")
equal(Model.parseIso(iso)?.timeIntervalSince1970 ?? 0, 1_760_000_000.5, "fast ISO parse")
check(Model.parseIso("2026-01-02T03:04:05+00:00") != nil, "ISO with offset")
check(Model.parseIso("2026-01-02T03:04:05") != nil, "ISO without zone")
check(Model.parseIso("ontem") == nil && Model.parseIso(5) == nil, "invalid dates")

// MARK: performance (100,000 notes)

do {
	let folder = tempFolder()
	var notes: [[String: Any]] = []
	for i in 0..<100_000 {
		notes.append(["id": "id\(i)", "title": "Folha \(i) reunião", "content": "<p>Texto da folha \(i) com <strong>ação</strong></p>", "tags": ["t\(i % 7)"], "laneId": Model.laneIds[i % 4], "notebookId": NSNull(), "folderId": NSNull(), "createdAt": "2026-01-01T00:00:00.000Z", "updatedAt": "2026-01-01T00:00:00.000Z"])
	}
	try JSONSerialization.data(withJSONObject: ["format": "notas-workflow", "version": 1, "folders": [Any](), "notebooks": [Any](), "notes": notes] as [String: Any]).write(to: URL(fileURLWithPath: (folder as NSString).appendingPathComponent(NotesStore.fileName)))
	var start = Date()
	let big = newStore(folder)
	let loadTime = Date().timeIntervalSince(start)
	equal(big.notes.count, 100_000, "100,000 notes read")
	print(String(format: "  ler 100 mil folhas: %.2f s", loadTime))
	let index = SearchIndex()
	start = Date()
	for note in big.notes {
		_ = index.entry(note)
	}
	print(String(format: "  preparar a busca: %.2f s", Date().timeIntervalSince(start)))
	start = Date()
	let found = Search.search(big.notes, "acao 99999", index: index)
	let searchTime = Date().timeIntervalSince(start)
	print(String(format: "  buscar: %.3f s", searchTime))
	check(searchTime < 1.0 && found.first?.note.id == "id99999", "search in 100,000 notes under 1 s")
	big.enableBackgroundSaving()
	start = Date()
	try big.moveNote("id5000", laneId: "done")
	_ = big.getNote("id99999")
	check(Date().timeIntervalSince(start) < 0.5, "status change is fast")
	start = Date()
	check(big.flush() == nil, "background write of 100,000 notes")
	print(String(format: "  gravar: %.2f s", Date().timeIntervalSince(start)))
	check(loadTime < 10, "reading 100,000 notes takes seconds at most")
} catch {
	check(false, "performance: \(error)")
}

print("\n\(passed) verificações passaram, \(failed.count) falharam.")
exit(failed.isEmpty ? 0 : 1)
