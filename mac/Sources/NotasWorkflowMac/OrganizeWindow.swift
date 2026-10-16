// Notas Workflow Mac - OrganizeWindow.swift
// "Notebooks and folders": a tree with each folder, its notebooks and the notes of each
// one, plus the notebooks without folder and the loose notes. Notes are added only when
// their branch is opened, in pages. Enter opens a note (port of organizeDialog.py).
// Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
// This file is covered by the GNU General Public License, version 2.

import AppKit
import NotasCore

final class OrganizeWindowController {
	/// Notes added to a branch at a time; "Show more notes" adds the next page.
	static let pageSize = 200

	unowned let controller: AppController
	let window = KeyWindow(title: ui("Notebooks and folders"))
	let tree = TreeView(label: accessibleName(ui("&Organization:")), width: 520, height: 340)
	var createButton: ActionButton!
	var renameButton: ActionButton!
	var moveButton: ActionButton!
	var deleteButton: ActionButton!
	/// key -> node of what is in the tree now.
	var nodes: [NodeKey: TreeNode] = [:]
	/// Notes shown in each branch (pages of pageSize) and branches whose notes were added.
	var shown: [NodeKey: Int] = [:]
	var loaded = Set<NodeKey>()
	var counts: (byNotebook: [String: Int], byFolder: [String: Int], loose: Int) = ([:], [:], 0)
	private var pending = false

	var store: NotesStore { controller.store }

	init(controller: AppController) {
		self.controller = controller
		createButton = ActionButton(ui("&Create…"), key: "n") { [unowned self] in self.onCreate() }
		renameButton = ActionButton(ui("&Rename…"), key: "r") { [unowned self] in self.onRename() }
		moveButton = ActionButton(ui("&Move to…")) { [unowned self] in self.onMove() }
		deleteButton = ActionButton(ui("&Delete")) { [unowned self] in self.onDelete() }
		let closeButton = ActionButton(ui("C&lose")) { [unowned self] in self.close() }
		layoutWindow(window, [
			makeLabel(ui("&Organization:")),
			tree.scroll,
			buttonRow([createButton, renameButton, moveButton, deleteButton, closeButton]),
		])
		tree.onSelectionChange = { [unowned self] in self.updateButtons() }
		tree.onWillExpand = { [unowned self] node in self.loadNotes(node.key) }
		tree.onActivate = { [unowned self] in self.activate() }
		window.keyHandler = { [unowned self] event in self.handleKey(event) }
		window.closeHandler = { [unowned self] in self.close() }
		refresh()
	}

	func run() {
		window.makeFirstResponder(tree.outline)
		runModalWindow(window)
	}

	func focusTree() {
		window.makeFirstResponder(tree.outline)
	}

	// MARK: tree

	func branchNotes(_ key: NodeKey) -> [Note] {
		switch key.kind {
		case "notebook": return store.notesIn(key.ident!)
		case "folder": return store.notesInFolder(key.ident!)
		case "loose": return store.looseNotes()
		default: return []
		}
	}

	@discardableResult
	func add(_ parent: TreeNode?, _ key: NodeKey, _ text: String, into roots: inout [TreeNode]) -> TreeNode {
		let node = TreeNode(key, text)
		if let parent {
			parent.append(node)
		} else {
			roots.append(node)
		}
		nodes[key] = node
		return node
	}

	/// Rebuilds the tree, keeping the open branches. select: a key such as ("folder", id),
	/// ("notebook", id) or ("note", id); nil keeps the selection.
	func refresh(select: NodeKey? = nil) {
		let toSelect = select ?? selectedKey()
		var expanded = nodes.filter { $0.key.kind != "note" && tree.isExpanded($0.value) }.map { $0.key }
		nodes = [:]
		loaded = []
		counts = store.placeCounts()
		var roots: [TreeNode] = []
		for folder in store.folders {
			let notebooks = store.notebooksIn(folder.id)
			let direct = counts.byFolder[folder.id] ?? 0
			let text = tr("Folder {name}, {notebooks}, {notes}", ["name": folder.name, "notebooks": Messages.notebooksCount(notebooks.count), "notes": Messages.notesCount(direct)])
			let node = add(nil, NodeKey("folder", folder.id), text, into: &roots)
			for nb in notebooks {
				addNotebook(node, nb, into: &roots)
			}
			node.hasChildren = !notebooks.isEmpty || direct > 0
		}
		let loose = store.notebooksIn(nil)
		let noFolder = add(nil, NodeKey("none"), tr("Without folder, {count}", ["count": Messages.notebooksCount(loose.count)]), into: &roots)
		for nb in loose {
			addNotebook(noFolder, nb, into: &roots)
		}
		noFolder.hasChildren = !loose.isEmpty
		let looseNode = add(nil, NodeKey("loose"), tr("Loose notes, {count}", ["count": Messages.notesCount(counts.loose)]), into: &roots)
		looseNode.hasChildren = counts.loose > 0
		if let toSelect, toSelect.kind == "note", let note = store.getNote(toSelect.ident) {
			expanded.append(branchOf(note))
		}
		tree.roots = roots
		tree.reload()
		if let key = toSelect, key.kind == "note" {
			// The page with the note to select is added before its branch opens.
			loadNotes(branchOf(store.getNote(key.ident)), until: key.ident)
		}
		// Folders first, so their notebooks are in the tree when they open.
		for key in expanded.sorted(by: { order($0) < order($1) }) {
			expandKey(key)
		}
		if let node = toSelect.flatMap({ nodes[$0] }) ?? roots.first {
			tree.select(node)
		}
		updateButtons()
	}

	private func order(_ key: NodeKey) -> Int {
		switch key.kind {
		case "folder", "none": return 0
		case "notebook": return 1
		default: return 2
		}
	}

	func addNotebook(_ parent: TreeNode, _ nb: Notebook, into roots: inout [TreeNode]) {
		let count = counts.byNotebook[nb.id] ?? 0
		let node = add(parent, NodeKey("notebook", nb.id), "\(nb.name), \(Messages.notesCount(count))", into: &roots)
		node.hasChildren = count > 0
	}

	func branchOf(_ note: Note?) -> NodeKey {
		guard let note else { return NodeKey("loose") }
		if let nb = note.notebookId {
			return NodeKey("notebook", nb)
		}
		if let f = note.folderId {
			return NodeKey("folder", f)
		}
		return NodeKey("loose")
	}

	/// Opens a branch (and the folder of a notebook), making sure its notes are there.
	func expandKey(_ key: NodeKey) {
		if key.kind == "notebook", let nb = store.getNotebook(key.ident) {
			expandKey(nb.folderId.map { NodeKey("folder", $0) } ?? NodeKey("none"))
		}
		guard let node = nodes[key] else { return }
		loadNotes(key)
		if !tree.isExpanded(node) {
			tree.expand(node)
		}
	}

	/// Adds the notes of a branch (the first page, or up to the page of note `until`).
	func loadNotes(_ key: NodeKey, until: String? = nil) {
		guard ["notebook", "folder", "loose"].contains(key.kind), !loaded.contains(key), let parent = nodes[key] else { return }
		loaded.insert(key)
		let notes = branchNotes(key)
		var count = shown[key] ?? Self.pageSize
		if let until, let i = notes.firstIndex(where: { $0.id == until }), i >= count {
			count = (i / Self.pageSize + 1) * Self.pageSize
		}
		shown[key] = count
		var unused: [TreeNode] = []
		for note in notes.prefix(count) {
			add(parent, NodeKey("note", note.id), Messages.noteDescription(note, place: "", withLane: true), into: &unused)
		}
		if notes.count > count {
			let more = add(parent, NodeKey("more", "\(key.kind):\(key.ident ?? "")"), Messages.moreNotes(notes.count - count, Self.pageSize), into: &unused)
			more.moreOf = key
		}
		tree.reload(parent)
	}

	func selectedKey() -> NodeKey? {
		tree.selected?.key
	}

	func selected() -> (String?, String?) {
		guard let key = selectedKey() else { return (nil, nil) }
		return (key.kind, key.ident)
	}

	func updateButtons() {
		let (kind, _) = selected()
		let editable = kind == "folder" || kind == "notebook" || kind == "note"
		renameButton.isEnabled = editable
		deleteButton.isEnabled = editable
		moveButton.isEnabled = kind == "note" || (kind == "notebook" && !store.folders.isEmpty)
	}

	/// (notebookId, folderId) where a new note goes, from the selection.
	func place() -> (String?, String?) {
		let (kind, ident) = selected()
		switch kind {
		case "notebook": return (ident, nil)
		case "folder": return (nil, ident)
		case "note":
			guard let note = store.getNote(ident) else { return (nil, nil) }
			return (note.notebookId, note.folderId)
		default: return (nil, nil)
		}
	}

	func targetFolder() -> String? {
		let (kind, ident) = selected()
		if kind == "folder" {
			return ident
		}
		let (notebookId, folderId) = place()
		if let notebookId {
			return store.getNotebook(notebookId)?.folderId
		}
		return folderId
	}

	// MARK: keyboard

	func handleKey(_ event: NSEvent) -> Bool {
		let mods = event.shortcutModifiers
		if mods == [.command, .shift] && event.lowerChars == "m" {
			onMove()
			return true
		}
		if mods == .command && event.isDelete {
			onDelete()
			return true
		}
		guard window.firstResponder === tree.outline, mods.isEmpty else { return false }
		if event.isReturn {
			activate()
			return true
		}
		if event.isDelete {
			onDelete()
			return true
		}
		if event.keyCode == KeyCode.f2 {
			onRename()
			return true
		}
		return false
	}

	/// Enter or double click: opens the note, shows more notes or opens/closes the branch.
	func activate() {
		if pending {
			return
		}
		guard let node = tree.selected else { return }
		switch node.key.kind {
		case "note":
			pending = true
			let noteId = node.key.ident!
			DispatchQueue.main.async {
				self.openNote(noteId)
			}
		case "more":
			if let branch = node.moreOf {
				showMore(branch)
			}
		default:
			tree.toggle(node)
		}
	}

	func openNote(_ noteId: String) {
		defer { pending = false }
		controller.editNote(noteId)
		refresh(select: store.getNote(noteId) != nil ? NodeKey("note", noteId) : nil)
		focusTree()
	}

	func showMore(_ key: NodeKey) {
		let notes = branchNotes(key)
		let first = shown[key] ?? Self.pageSize
		shown[key] = first + Self.pageSize
		refresh(select: first < notes.count ? NodeKey("note", notes[first].id) : key)
	}

	// MARK: actions

	func onCreate() {
		let index = Prompts.chooseFromMenu(createButton, Messages.createLabels())
		if index == 0 {
			let (notebookId, folderId) = place()
			if let noteId = controller.newNote(laneId: Model.defaultLane, notebookId: notebookId, folderId: folderId) {
				refresh(select: NodeKey("note", noteId))
			}
		} else if index == 1 {
			if let notebook = controller.createNotebook(folderId: targetFolder()) {
				refresh(select: NodeKey("notebook", notebook.id))
			}
		} else if index == 2 {
			if let folder = controller.createFolder() {
				refresh(select: NodeKey("folder", folder.id))
			}
		}
		focusTree()
	}

	func onRename() {
		let (selectedKind, selectedIdent) = selected()
		defer { focusTree() }
		if selectedKind == "note", let ident = selectedIdent, let note = store.getNote(ident) {
			guard let title = Prompts.askText(tr("New title:"), tr("Rename"), value: note.title, maxLength: Model.maxTitle) else { return }
			let clean = title.trimmingCharacters(in: .whitespaces)
			guard !clean.isEmpty, clean != note.title else { return }
			if controller.safe({ try store.updateNote(ident, NotePatch(title: title)) }) != nil {
				refresh(select: NodeKey("note", ident))
				controller.speak(tr("Renamed to {name}", ["name": store.getNote(ident)?.title ?? clean]))
			}
			return
		}
		guard let kind = selectedKind, let ident = selectedIdent, kind == "folder" || kind == "notebook" else { return }
		let current = kind == "folder" ? store.getFolder(ident)?.name : store.getNotebook(ident)?.name
		guard let current, let name = Prompts.askText(tr("New name:"), tr("Rename"), value: current) else { return }
		let clean = name.trimmingCharacters(in: .whitespaces)
		guard !clean.isEmpty, clean != current else { return }
		let done = controller.safe {
			if kind == "folder" {
				try store.renameFolder(ident, name)
			} else {
				try store.renameNotebook(ident, name)
			}
		}
		if done != nil {
			refresh(select: NodeKey(kind, ident))
			let newName = kind == "folder" ? store.getFolder(ident)?.name : store.getNotebook(ident)?.name
			controller.speak(tr("Renamed to {name}", ["name": newName ?? clean]))
		}
	}

	func onMove() {
		let (selectedKind, selectedIdent) = selected()
		defer { focusTree() }
		if selectedKind == "note", let ident = selectedIdent, let note = store.getNote(ident) {
			if controller.moveNote(note) {
				refresh(select: NodeKey("note", ident))
			}
			return
		}
		guard selectedKind == "notebook", let ident = selectedIdent, let notebook = store.getNotebook(ident) else { return }
		let labels = [tr("Without folder")] + store.folders.map(\.name)
		let ids: [String?] = [nil] + store.folders.map { Optional($0.id) }
		let current = ids.firstIndex(where: { $0 == notebook.folderId }) ?? 0
		guard let index = Prompts.chooseItem(tr("Folder of the notebook {name}:", ["name": notebook.name]), tr("Move to folder"), labels, current: current),
			ids[index] != notebook.folderId else { return }
		if controller.safe({ try store.moveNotebookToFolder(ident, ids[index]) }) != nil {
			refresh(select: NodeKey("notebook", ident))
			controller.speak(Messages.movedToPlace(labels[index]))
		}
	}

	func onDelete() {
		let (selectedKind, selectedIdent) = selected()
		defer { focusTree() }
		if selectedKind == "note", let ident = selectedIdent, let note = store.getNote(ident) {
			let branch = branchOf(note)
			if controller.deleteNote(note) {
				refresh(select: branch)
			}
			return
		}
		guard let kind = selectedKind, let ident = selectedIdent, kind == "folder" || kind == "notebook" else { return }
		let name: String
		let question: String
		if kind == "folder" {
			guard let folder = store.getFolder(ident) else { return }
			name = folder.name
			question = tr("Delete the folder {name}? Its notebooks and notes are not deleted: they stay without folder.", ["name": name])
		} else {
			guard let notebook = store.getNotebook(ident) else { return }
			name = notebook.name
			question = tr("Delete the notebook {name}? Its notes are not deleted: they become loose notes.", ["name": name])
		}
		guard Prompts.confirm(question, tr("Delete")) else { return }
		let done = controller.safe {
			if kind == "folder" {
				try store.deleteFolder(ident)
			} else {
				try store.deleteNotebook(ident)
			}
		}
		if done != nil {
			nodes.removeValue(forKey: NodeKey(kind, ident))
			refresh(select: NodeKey("none"))
			controller.speak(tr("{name} deleted", ["name": name]))
		}
	}

	func close() {
		endModalWindow(window)
	}
}
