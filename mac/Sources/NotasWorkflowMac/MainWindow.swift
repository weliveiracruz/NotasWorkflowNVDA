// Notas Workflow Mac - MainWindow.swift
// The "Notas Workflow" window: the notes in a tree of status lanes (port of mainDialog.py).
// Long lanes are shown in pages, so the window stays fast with 100,000 notes.
// Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
// This file is covered by the GNU General Public License, version 2.

import AppKit
import NotasCore

final class MainWindowController {
	/// Notes added to a lane at a time; "Show more notes" adds the next page.
	static let pageSize = 200
	/// The window is kept (hidden) after Close: showing it again is instant.
	static var instance: MainWindowController?

	static func open() {
		let controller = AppController.shared
		if let main = instance {
			if controller.reloadIfChanged() {
				main.refresh(selectId: main.selectedNoteId())
			}
			main.show()
			return
		}
		controller.reloadIfChanged()
		let main = MainWindowController(controller: controller)
		instance = main
		main.window.center()
		main.show()
	}

	unowned let controller: AppController
	let window = KeyWindow(title: Messages.appName)
	let filterChoice: ChoiceBox
	let treeLabel = makeLabel("")
	let tree: TreeView
	var createButton: ActionButton!
	var statusButton: ActionButton!
	var moveButton: ActionButton!
	var deleteButton: ActionButton!

	var filters: [NoteFilter] = [.all]
	var activeFilter: NoteFilter = .all
	var visibleIds: [String] = []
	/// Notes shown in each lane (pages of pageSize).
	var shown: [String: Int] = [:]
	/// Tree nodes: note id -> node and lane id -> lane node (to change one note without rebuilding).
	var items: [String: TreeNode] = [:]
	var laneNodes: [String: TreeNode] = [:]
	/// Lanes the person opened. The lanes start closed (only the lane of a note being
	/// selected opens by itself), and stay as the person left them.
	var expandedLanes = Set<String>()
	/// An Enter or a double click already asked to open something (avoids opening twice).
	private var pending = false

	var store: NotesStore { controller.store }

	init(controller: AppController) {
		self.controller = controller
		filterChoice = ChoiceBox(items: [], label: accessibleName(ui("&Show:")))
		tree = TreeView(label: "", width: 620, height: 360)
		createButton = ActionButton(ui("&Create…"), key: "n") { [unowned self] in self.onCreate() }
		statusButton = ActionButton(ui("&Update the task status…"), key: "u") { [unowned self] in self.onStatus() }
		moveButton = ActionButton(ui("&Move to…")) { [unowned self] in self.onMove() }
		deleteButton = ActionButton(ui("&Delete")) { [unowned self] in self.onDelete() }
		let searchButton = ActionButton(ui("Searc&h…"), key: "f") { [unowned self] in self.onSearch() }
		let organizeButton = ActionButton(ui("Notebooks and &folders…"), key: "o") { [unowned self] in self.onOrganize() }
		let closeButton = ActionButton(ui("C&lose")) { [unowned self] in self.hide() }
		layoutWindow(window, [
			labelledRow(ui("&Show:"), filterChoice),
			treeLabel,
			tree.scroll,
			buttonRow([createButton, statusButton, moveButton, deleteButton]),
			buttonRow([searchButton, organizeButton, closeButton]),
		])
		window.setFrameAutosaveName("NotasWorkflowMainWindow")
		filterChoice.onChange = { [unowned self] in
			self.setFilter(self.filters[max(0, self.filterChoice.indexOfSelectedItem)])
		}
		tree.onActivate = { [unowned self] in self.activate() }
		tree.onSelectionChange = { [unowned self] in self.updateButtons() }
		tree.onExpanded = { [unowned self] node, opened in self.onLaneOpened(node, opened) }
		window.keyHandler = { [unowned self] event in self.handleKey(event) }
		window.closeHandler = { [unowned self] in self.hide() }
		refresh()
	}

	func show() {
		NSApp.activate(ignoringOtherApps: true)
		window.makeKeyAndOrderFront(nil)
		focusNotes()
	}

	/// Close (and Esc) only hide the window: building the tree again with many notes would take time.
	func hide() {
		window.orderOut(nil)
	}

	func focusNotes() {
		window.makeFirstResponder(tree.outline)
	}

	// MARK: filters

	func filterLabel(_ filter: NoteFilter) -> String {
		switch filter {
		case .loose: return tr("Loose notes")
		case .recent: return tr("Recent notes")
		case .notebook(let id): return tr("Notebook: {name}", ["name": store.notebookName(id)])
		case .folder(let id): return tr("Folder: {name}", ["name": store.getFolder(id)?.name ?? ""])
		case .all: return tr("All notes")
		}
	}

	func rebuildFilters() {
		filters = [.all, .loose, .recent]
		filters += store.notebooks.map { .notebook($0.id) }
		filters += store.folders.map { .folder($0.id) }
		if !filters.contains(activeFilter) {
			activeFilter = .all
		}
		let labels = filters.map(filterLabel)
		if labels != filterChoice.titles {
			filterChoice.setItems(labels)
		}
		filterChoice.selectItem(at: filters.firstIndex(of: activeFilter) ?? 0)
	}

	func setFilter(_ filter: NoteFilter) {
		activeFilter = filter
		shown = [:]
		refresh()
	}

	// MARK: content

	/// Notes of the filter by lane, the label with their number, and the pages that must be
	/// shown so that selectId is in the tree.
	func prepare(_ selectId: String?) -> [String: [Note]] {
		let notes = store.filtered(activeFilter)
		let lanes = Model.byLane(notes)
		visibleIds = Model.laneIds.flatMap { lanes[$0]!.map(\.id) }
		let label = ui("Not&es: {filter} ({count})", ["filter": filterLabel(activeFilter), "count": notes.count])
		treeLabel.stringValue = label
		tree.outline.setAccessibilityLabel(accessibleName(label))
		for lane in Model.laneIds {
			var count = shown[lane] ?? Self.pageSize
			if let selectId, let i = lanes[lane]!.firstIndex(where: { $0.id == selectId }), i >= count {
				count = (i / Self.pageSize + 1) * Self.pageSize
			}
			shown[lane] = count
		}
		return lanes
	}

	/// Rebuilds the whole tree keeping (or choosing) the selection.
	func refresh(selectId: String? = nil, selectLane: String? = nil) {
		rebuildFilters()
		let lanes = prepare(selectId)
		fillTree(lanes, selectId, selectLane)
		updateButtons()
	}

	/// Rebuilds only some lanes (a status change touches two): fast with many notes.
	func refreshLanes(_ changed: Set<String>, selectId: String? = nil, selectLane: String? = nil) {
		if laneNodes.isEmpty || activeFilter == .recent {
			refresh(selectId: selectId, selectLane: selectLane)
			return
		}
		let lanes = prepare(selectId)
		var toSelect: TreeNode?
		for lane in Model.laneIds where changed.contains(lane) {
			let node = laneNodes[lane]!
			for child in node.children where child.key.kind == "note" {
				items.removeValue(forKey: child.key.ident!)
			}
			node.children = []
			let found = fillLane(node, lane, lanes[lane]!, selectId)
			tree.reload(node)
			// Rebuilt lanes stay as the person left them.
			if expandedLanes.contains(lane) {
				tree.expand(node)
			}
			toSelect = toSelect ?? found
			if lane == selectLane && selectId == nil {
				toSelect = node
			}
		}
		if toSelect == nil, let selectId, let node = items[selectId] {
			toSelect = node
		}
		if let toSelect {
			tree.select(toSelect)
		}
		updateButtons()
	}

	/// Adds the shown page of a lane. Returns the node of selectId, if it is there.
	@discardableResult
	func fillLane(_ node: TreeNode, _ lane: String, _ notes: [Note], _ selectId: String?) -> TreeNode? {
		node.text = Messages.laneNode(lane, notes.count)
		var found: TreeNode?
		let count = shown[lane] ?? Self.pageSize
		for note in notes.prefix(count) {
			let child = node.append(TreeNode(NodeKey("note", note.id), Messages.noteDescription(note, place: Messages.placeOf(store, note))))
			items[note.id] = child
			if note.id == selectId {
				found = child
			}
		}
		if notes.count > count {
			let more = node.append(TreeNode(NodeKey("more", lane), Messages.moreNotes(notes.count - count, Self.pageSize)))
			more.moreOf = NodeKey("lane", lane)
		}
		node.hasChildren = !notes.isEmpty
		return found
	}

	func onLaneOpened(_ node: TreeNode, _ opened: Bool) {
		guard node.key.kind == "lane", let lane = node.key.ident else { return }
		if opened {
			expandedLanes.insert(lane)
		} else {
			expandedLanes.remove(lane)
		}
	}

	func fillTree(_ lanes: [String: [Note]], _ selectId: String?, _ selectLane: String?) {
		items = [:]
		laneNodes = [:]
		var roots: [TreeNode] = []
		var toSelect: TreeNode?
		for lane in Model.laneIds {
			let node = TreeNode(NodeKey("lane", lane), "")
			laneNodes[lane] = node
			roots.append(node)
			let found = fillLane(node, lane, lanes[lane]!, selectId)
			toSelect = toSelect ?? found
			if lane == selectLane && selectId == nil {
				toSelect = node
			}
		}
		tree.roots = roots
		tree.reload()
		for lane in Model.laneIds where expandedLanes.contains(lane) {
			tree.expand(laneNodes[lane]!)
		}
		// Without a note to select, the focus is on the first lane (all lanes closed).
		if let node = toSelect ?? roots.first {
			tree.select(node)
		}
	}

	func isShown(_ note: Note) -> Bool {
		if activeFilter == .recent {
			return store.filtered(.recent).contains { $0.id == note.id }
		}
		return !Model.filterNotes([note], notebooks: store.notebooks, filter: activeFilter).isEmpty
	}

	/// After one note changed (title, tags, status, place or deleted): updates only what is
	/// needed. fallback: the note to select if this one left the list.
	func noteChanged(_ noteId: String, fallback: String? = nil) {
		let note = store.getNote(noteId)
		guard let node = items[noteId], let laneNode = node.parent else {
			if let note, isShown(note) {
				refreshLanes([note.laneId], selectId: noteId)
			}
			return
		}
		let oldLane = laneNode.key.ident ?? Model.defaultLane
		if note == nil || !isShown(note!) {
			let following = fallback ?? neighbourOf(noteId)
			refreshLanes([oldLane], selectId: following, selectLane: following == nil ? oldLane : nil)
		} else if note!.laneId != oldLane {
			refreshLanes([oldLane, note!.laneId], selectId: noteId)
		} else {
			tree.setText(node, Messages.noteDescription(note!, place: Messages.placeOf(store, note!)))
			updateButtons()
		}
	}

	func selectedKey() -> NodeKey? {
		tree.selected?.key
	}

	func selectedNoteId() -> String? {
		guard let key = selectedKey(), key.kind == "note" else { return nil }
		return key.ident
	}

	func selectedLane() -> String {
		guard let key = selectedKey() else { return Model.defaultLane }
		if key.kind == "note", let note = store.getNote(key.ident) {
			return note.laneId
		}
		return key.ident ?? Model.defaultLane
	}

	func updateButtons() {
		let hasNote = selectedNoteId() != nil
		for button in [statusButton, moveButton, deleteButton] {
			button?.isEnabled = hasNote
		}
	}

	/// The note that takes the place of noteId in the list (next, otherwise previous).
	func neighbourOf(_ noteId: String) -> String? {
		guard let i = visibleIds.firstIndex(of: noteId) else { return nil }
		if i + 1 < visibleIds.count {
			return visibleIds[i + 1]
		}
		return i > 0 ? visibleIds[i - 1] : nil
	}

	/// The note after noteId in its lane (the next one in the pile), otherwise the one before
	/// it, or nil when it is alone in the lane.
	func nextInLane(_ noteId: String) -> String? {
		guard let note = store.getNote(noteId) else { return nil }
		let ids = Model.byLane(store.filtered(activeFilter))[note.laneId]!.map(\.id)
		guard let i = ids.firstIndex(of: noteId) else { return nil }
		if i + 1 < ids.count {
			return ids[i + 1]
		}
		return i > 0 ? ids[i - 1] : nil
	}

	/// Shows the next page of a lane, with the focus on its first new note.
	func showMore(_ lane: String) {
		let notes = Model.byLane(store.filtered(activeFilter))[lane]!
		let first = shown[lane] ?? Self.pageSize
		shown[lane] = first + Self.pageSize
		refresh(selectId: first < notes.count ? notes[first].id : nil)
	}

	// MARK: keyboard

	/// Enter opens, Delete deletes, Option+Shift+Arrows change the status. True when handled.
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
		guard window.firstResponder === tree.outline else { return false }
		if event.isReturn && mods.isEmpty {
			activate()
			return true
		}
		if event.isDelete && mods.isEmpty {
			onDelete()
			return true
		}
		if mods == [.option, .shift] && (event.keyCode == KeyCode.left || event.keyCode == KeyCode.right) {
			moveBy(event.keyCode == KeyCode.right ? 1 : -1)
			return true
		}
		return false
	}

	/// Enter or double click: opens the note, shows more notes or opens/closes the lane.
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
			showMore(node.key.ident!)
		default:
			tree.toggle(node)
		}
	}

	func openNote(_ noteId: String) {
		defer { pending = false }
		let before = store.getNote(noteId)
		let lane = before?.laneId
		let following = nextInLane(noteId)
		controller.editNote(noteId)
		let after = store.getNote(noteId)
		if let after, after.laneId == lane, isShown(after) {
			// Still in the same place of the pile: the focus comes back to it.
			noteChanged(noteId)
			if let node = items[noteId] {
				tree.select(node)
			}
		} else {
			// Moved to another status (or out of what is shown): the focus goes to the next
			// note of the pile it was in (the previous one if it was the last).
			var changed = Set<String>()
			if let lane {
				changed.insert(lane)
			}
			if let after {
				changed.insert(after.laneId)
			}
			refreshLanes(changed, selectId: following, selectLane: following == nil ? lane : nil)
		}
		focusNotes()
	}

	// MARK: actions

	func onCreate() {
		let index = Prompts.chooseFromMenu(createButton, Messages.createLabels())
		var notebookId: String?
		var folderId: String?
		switch activeFilter {
		case .notebook(let id): notebookId = id
		case .folder(let id): folderId = id
		default: break
		}
		if index == 0 {
			if let noteId = controller.newNote(laneId: selectedLane(), notebookId: notebookId, folderId: folderId) {
				if !store.filtered(activeFilter).contains(where: { $0.id == noteId }) {
					activeFilter = .all
				}
				refresh(selectId: noteId)
			}
		} else if index == 1 {
			if controller.createNotebook(folderId: folderId) != nil {
				refresh(selectId: selectedNoteId())
			}
		} else if index == 2 {
			if controller.createFolder() != nil {
				refresh(selectId: selectedNoteId())
			}
		}
		focusNotes()
	}

	func setStatus(_ noteId: String, _ laneId: String) {
		if controller.safe({ try store.moveNote(noteId, laneId: laneId) }) != nil {
			noteChanged(noteId)
			controller.speak(Messages.movedTo(laneId))
		}
		focusNotes()
	}

	func moveBy(_ step: Int) {
		guard let noteId = selectedNoteId(), let note = store.getNote(noteId) else { return }
		guard let target = Model.neighbourLane(note.laneId, step) else {
			controller.speak(step > 0 ? Messages.alreadyLast() : Messages.alreadyFirst())
			return
		}
		setStatus(noteId, target)
	}

	func onStatus() {
		guard let noteId = selectedNoteId(), let note = store.getNote(noteId) else { return }
		let others = Model.laneIds.filter { $0 != note.laneId }
		guard let index = Prompts.chooseFromMenu(statusButton, others.map(Messages.laneName)) else {
			focusNotes()
			return
		}
		setStatus(noteId, others[index])
	}

	func onMove() {
		guard let noteId = selectedNoteId(), let note = store.getNote(noteId) else { return }
		let following = neighbourOf(noteId)
		if controller.moveNote(note) {
			noteChanged(noteId, fallback: following)
		}
		focusNotes()
	}

	func onDelete() {
		guard let noteId = selectedNoteId(), let note = store.getNote(noteId) else { return }
		let following = neighbourOf(noteId)
		if controller.deleteNote(note) {
			noteChanged(noteId, fallback: following)
		}
		focusNotes()
	}

	func onSearch() {
		let opened = controller.openSearch()
		refresh(selectId: opened ?? selectedNoteId())
		focusNotes()
	}

	func onOrganize() {
		OrganizeWindowController(controller: controller).run()
		refresh(selectId: selectedNoteId())
		focusNotes()
	}
}
