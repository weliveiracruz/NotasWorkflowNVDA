// Notas Workflow Mac - SearchWindow.swift
// "Search notes": searches while typing (300 ms), results with excerpt and relevance
// (port of searchDialog.py).
// Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
// This file is covered by the GNU General Public License, version 2.

import AppKit
import NotasCore

final class SearchWindowController: NSObject, NSTableViewDataSource, NSTableViewDelegate {
	/// Pause in the typing before searching.
	static let debounce = 0.3

	unowned let controller: AppController
	let window = KeyWindow(title: ui("Search notes"))
	let queryEdit = TextField(label: accessibleName(ui("&Search for:")), width: 560)
	let resultsLabel = makeLabel("")
	let table = NSTableView()
	let scroll = NSScrollView()
	var openButton: ActionButton!
	var rows: [(id: String, title: String, excerpt: String, relevance: String, date: String)] = []
	/// Id of the last note opened from the results (the main window selects it).
	var openedId: String?
	private var timer: Timer?

	init(controller: AppController, query: String = "") {
		self.controller = controller
		super.init()
		queryEdit.maxLength = Search.maxQuery
		for (id, title, width) in [
			("title", ui("Title"), 170.0),
			("excerpt", ui("Excerpt"), 250.0),
			("relevance", ui("Relevance"), 70.0),
			("updated", ui("Updated on"), 80.0),
		] {
			let column = NSTableColumn(identifier: NSUserInterfaceItemIdentifier(id))
			column.title = title
			column.width = CGFloat(width)
			table.addTableColumn(column)
		}
		table.allowsMultipleSelection = false
		table.usesAlternatingRowBackgroundColors = true
		table.dataSource = self
		table.delegate = self
		table.target = self
		table.doubleAction = #selector(doubleClicked)
		scroll.documentView = table
		scroll.hasVerticalScroller = true
		scroll.borderType = .bezelBorder
		scroll.translatesAutoresizingMaskIntoConstraints = false
		scroll.widthAnchor.constraint(greaterThanOrEqualToConstant: 580).isActive = true
		scroll.heightAnchor.constraint(greaterThanOrEqualToConstant: 300).isActive = true
		openButton = ActionButton(ui("&Open"), key: "o") { [unowned self] in self.onOpen() }
		let closeButton = ActionButton(ui("C&lose")) { [unowned self] in self.close() }
		setResultsLabel(0)
		layoutWindow(window, [
			labelledRow(ui("&Search for:"), queryEdit),
			resultsLabel,
			scroll,
			buttonRow([openButton, closeButton]),
		])
		queryEdit.onChange = { [unowned self] in self.scheduleSearch() }
		queryEdit.onEnter = { [unowned self] in
			self.runSearch()
			if !self.rows.isEmpty {
				self.window.makeFirstResponder(self.table)
			}
			return true
		}
		window.keyHandler = { [unowned self] event in
			if self.window.firstResponder === self.table && event.isReturn && event.shortcutModifiers.isEmpty {
				self.onOpen()
				return true
			}
			return false
		}
		window.closeHandler = { [unowned self] in self.close() }
		updateButtons()
		if !query.isEmpty {
			queryEdit.stringValue = query
			runSearch(announce: false)
		}
	}

	func run() {
		window.makeFirstResponder(queryEdit)
		runModalWindow(window)
		timer?.invalidate()
	}

	func setResultsLabel(_ count: Int) {
		let text = ui("&Results ({count}):", ["count": count])
		resultsLabel.stringValue = text
		table.setAccessibilityLabel(accessibleName(text))
	}

	func updateButtons() {
		openButton.isEnabled = table.selectedRow >= 0
	}

	func scheduleSearch() {
		timer?.invalidate()
		let t = Timer(timeInterval: Self.debounce, repeats: false) { [weak self] _ in
			self?.runSearch()
		}
		RunLoop.main.add(t, forMode: .common)
		timer = t
	}

	@discardableResult
	func runSearch(announce: Bool = true) -> [SearchResult] {
		timer?.invalidate()
		let query = queryEdit.stringValue
		let notes = controller.store.notes
		let index = controller.searchIndex
		let found = Search.search(notes, query, index: index)
		if index.count > notes.count + 1000 {
			// Many notes were deleted or replaced: drop their prepared text.
			index.forget(keep: Set(notes.map(\.id)))
		}
		rows = found.map { r in
			(id: r.note.id, title: Messages.noteTitle(r.note), excerpt: r.excerpt, relevance: "\(Int((r.score * 100).rounded()))%", date: Messages.formatDate(r.note.updatedAt))
		}
		table.reloadData()
		if !rows.isEmpty {
			table.selectRowIndexes(IndexSet(integer: 0), byExtendingSelection: false)
			table.scrollRowToVisible(0)
		}
		setResultsLabel(rows.count)
		updateButtons()
		if announce && !query.trimmingCharacters(in: .whitespaces).isEmpty {
			if rows.isEmpty {
				controller.speak(tr("No note found"))
			} else {
				controller.speak(tr("{count} found", ["count": Messages.notesCount(rows.count)]))
			}
		}
		return found
	}

	@objc func doubleClicked() {
		if table.clickedRow >= 0 {
			onOpen()
		}
	}

	func onOpen() {
		let row = table.selectedRow
		guard row >= 0 && row < rows.count else { return }
		let noteId = rows[row].id
		openedId = noteId
		controller.editNote(noteId)
		// The note may have changed (or been deleted): search again, keeping the place.
		runSearch(announce: false)
		if let again = rows.firstIndex(where: { $0.id == noteId }) {
			table.selectRowIndexes(IndexSet(integer: again), byExtendingSelection: false)
			table.scrollRowToVisible(again)
		}
		window.makeFirstResponder(rows.isEmpty ? queryEdit : table)
	}

	func close() {
		timer?.invalidate()
		endModalWindow(window)
	}

	// MARK: table

	func numberOfRows(in tableView: NSTableView) -> Int {
		rows.count
	}

	func tableView(_ tableView: NSTableView, viewFor tableColumn: NSTableColumn?, row: Int) -> NSView? {
		guard let column = tableColumn, row < rows.count else { return nil }
		let id = column.identifier
		let cell = tableView.makeView(withIdentifier: id, owner: nil) as? NSTableCellView ?? {
			let cell = NSTableCellView()
			cell.identifier = id
			let text = NSTextField(labelWithString: "")
			text.lineBreakMode = .byTruncatingTail
			text.translatesAutoresizingMaskIntoConstraints = false
			cell.addSubview(text)
			cell.textField = text
			NSLayoutConstraint.activate([
				text.leadingAnchor.constraint(equalTo: cell.leadingAnchor, constant: 2),
				text.trailingAnchor.constraint(equalTo: cell.trailingAnchor, constant: -2),
				text.centerYAnchor.constraint(equalTo: cell.centerYAnchor),
			])
			return cell
		}()
		let r = rows[row]
		switch id.rawValue {
		case "title": cell.textField?.stringValue = r.title
		case "excerpt": cell.textField?.stringValue = r.excerpt
		case "relevance": cell.textField?.stringValue = r.relevance
		default: cell.textField?.stringValue = r.date
		}
		return cell
	}

	func tableViewSelectionDidChange(_ notification: Notification) {
		updateButtons()
	}
}
