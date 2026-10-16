// Notas Workflow Mac - NoteWindow.swift
// "New note" and the note window: title, location (notebook or folder), status, tags,
// content, formatting and automatic saving (port of noteDialog.py).
// Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
// This file is covered by the GNU General Public License, version 2.

import AppKit
import NotasCore

struct NewNoteValues {
	let title: String
	let notebookId: String?
	let folderId: String?
	let laneId: String
}

final class NewNoteWindowController {
	let window = KeyWindow(title: ui("New note"), resizable: false)
	let titleEdit = TextField(label: accessibleName(ui("&Title:")), width: 380)
	let locationChoice: ChoiceBox
	let laneChoice: ChoiceBox
	let places: [Messages.Place]
	var createButton: ActionButton!
	private var accepted = false

	init(store: NotesStore, laneId: String, notebookId: String?, folderId: String?) {
		let (labels, places) = Messages.locationChoices(store)
		self.places = places
		locationChoice = ChoiceBox(items: labels, label: accessibleName(ui("&Location:")))
		let (nb, f) = store.location(notebookId: notebookId, folderId: folderId)
		locationChoice.selectItem(at: places.firstIndex(of: Messages.Place(notebookId: nb, folderId: f)) ?? 0)
		laneChoice = ChoiceBox(items: Messages.laneNames(), label: accessibleName(ui("&Status:")))
		laneChoice.selectItem(at: Model.laneIndex(laneId))
		titleEdit.maxLength = Model.maxTitle
		createButton = ActionButton(ui("C&reate"), key: "\r", modifiers: []) { [unowned self] in
			self.accept()
		}
		let cancel = ActionButton(ui("Cancel")) { [unowned self] in
			endModalWindow(self.window)
		}
		titleEdit.onChange = { [unowned self] in self.onTitle() }
		titleEdit.onEnter = { [unowned self] in
			self.accept()
			return true
		}
		layoutWindow(window, [
			labelledRow(ui("&Title:"), titleEdit),
			labelledRow(ui("&Location:"), locationChoice),
			labelledRow(ui("&Status:"), laneChoice),
			buttonRow([cancel, createButton]),
		])
		onTitle()
		window.initialFirstResponder = titleEdit
	}

	func onTitle() {
		createButton.isEnabled = !titleEdit.stringValue.trimmingCharacters(in: .whitespaces).isEmpty
	}

	func accept() {
		guard createButton.isEnabled else { return }
		accepted = true
		endModalWindow(window)
	}

	/// The values typed, or nil when cancelled.
	func run() -> NewNoteValues? {
		window.makeFirstResponder(titleEdit)
		runModalWindow(window)
		guard accepted else { return nil }
		let place = places[max(0, locationChoice.indexOfSelectedItem)]
		return NewNoteValues(
			title: titleEdit.stringValue.trimmingCharacters(in: .whitespaces),
			notebookId: place.notebookId,
			folderId: place.folderId,
			laneId: Model.laneIds[max(0, laneChoice.indexOfSelectedItem)]
		)
	}
}

/// The note window. Saves by itself some seconds after the last change and always saves
/// what is pending when it is closed.
final class NoteWindowController {
	static let shortcuts = ["bold": "⌘B", "italic": "⌘I"]

	unowned let controller: AppController
	let noteId: String
	let window: KeyWindow
	let titleEdit = TextField(label: accessibleName(ui("&Title:")), width: 520)
	let locationChoice: ChoiceBox
	let laneChoice: ChoiceBox
	let tagsEdit = TextField(label: accessibleName(ui("Ta&gs (comma separated):")), width: 520)
	let contentEdit = TextArea(label: accessibleName(ui("&Content:")), width: 520, height: 300)
	let statusEdit = NSTextField(labelWithString: "")
	var formatButton: ActionButton!
	let places: [Messages.Place]
	var dirty = Set<String>()
	private var loading = true
	private var timer: Timer?

	var store: NotesStore { controller.store }

	init(controller: AppController, noteId: String) {
		self.controller = controller
		self.noteId = noteId
		let note = controller.store.getNote(noteId)
		window = KeyWindow(title: Messages.noteTitle(note))
		let (labels, places) = Messages.locationChoices(controller.store)
		self.places = places
		locationChoice = ChoiceBox(items: labels, label: accessibleName(ui("&Location:")))
		laneChoice = ChoiceBox(items: Messages.laneNames(), label: accessibleName(ui("&Status:")))
		titleEdit.maxLength = Model.maxTitle
		// The save status can be read like a text (in the add-on it is a read-only field).
		statusEdit.isSelectable = true
		statusEdit.setAccessibilityLabel(accessibleName(ui("Save stat&us:")))
		formatButton = ActionButton(ui("&Formatting…")) { [unowned self] in
			self.onFormatButton()
		}
		let saveButton = ActionButton(ui("Sa&ve and close"), key: "\r", modifiers: [.command]) { [unowned self] in
			self.finish()
		}
		layoutWindow(window, [
			labelledRow(ui("&Title:"), titleEdit),
			labelledRow(ui("&Location:"), locationChoice),
			labelledRow(ui("&Status:"), laneChoice),
			labelledRow(ui("Ta&gs (comma separated):"), tagsEdit),
			labelledBlock(ui("&Content:"), contentEdit),
			formatButton,
			labelledRow(ui("Save stat&us:"), statusEdit),
			buttonRow([saveButton]),
		])
		titleEdit.onChange = { [unowned self] in self.onChange("title") }
		locationChoice.onChange = { [unowned self] in self.onChange("location") }
		laneChoice.onChange = { [unowned self] in self.onChange("laneId") }
		tagsEdit.onChange = { [unowned self] in self.onChange("tags") }
		contentEdit.onChange = { [unowned self] in self.onChange("content") }
		window.keyHandler = { [unowned self] event in self.handleKey(event) }
		window.closeHandler = { [unowned self] in self.finish() }
		if let note {
			load(note)
		}
	}

	func load(_ note: Note) {
		loading = true
		titleEdit.stringValue = note.title
		locationChoice.selectItem(at: places.firstIndex(of: Messages.placeOfNote(note)) ?? 0)
		laneChoice.selectItem(at: Model.laneIndex(note.laneId))
		tagsEdit.stringValue = note.tags.joined(separator: ", ")
		contentEdit.string = Markup.htmlToText(note.content)
		contentEdit.textView.setSelectedRange(NSRange(location: 0, length: 0))
		setStatus(tr("Saved"))
		dirty.removeAll()
		loading = false
	}

	func setStatus(_ text: String) {
		statusEdit.stringValue = text
		statusEdit.setAccessibilityValue(text)
	}

	func run(focusContent: Bool) {
		window.initialFirstResponder = focusContent ? contentEdit.textView : titleEdit
		window.makeFirstResponder(focusContent ? contentEdit.textView : titleEdit)
		runModalWindow(window)
		timer?.invalidate()
	}

	func onChange(_ field: String) {
		if loading {
			return
		}
		dirty.insert(field)
		setStatus(tr("Unsaved changes…"))
		timer?.invalidate()
		let t = Timer(timeInterval: TimeInterval(Settings.autoSaveSeconds), repeats: false) { [weak self] _ in
			self?.save(announce: Settings.announceAutoSave)
		}
		// Common modes: the timer also runs while the window is modal.
		RunLoop.main.add(t, forMode: .common)
		timer = t
	}

	func patch() -> NotePatch {
		var p = NotePatch()
		if dirty.contains("title") {
			p.title = titleEdit.stringValue
		}
		if dirty.contains("laneId") {
			p.laneId = Model.laneIds[max(0, laneChoice.indexOfSelectedItem)]
		}
		if dirty.contains("tags") {
			p.tags = Model.cleanTags(tagsEdit.stringValue)
		}
		if dirty.contains("content") {
			// Only an edited content is converted: imported HTML is kept as it is.
			p.content = Markup.textToHtml(contentEdit.string)
		}
		if dirty.contains("location") {
			let place = places[max(0, locationChoice.indexOfSelectedItem)]
			p.notebookId = .some(place.notebookId)
			p.folderId = .some(place.folderId)
		}
		return p
	}

	/// Writes the pending changes. Returns false when they could not be saved.
	@discardableResult
	func save(announce: Bool = false) -> Bool {
		timer?.invalidate()
		timer = nil
		if dirty.isEmpty {
			return true
		}
		if store.getNote(noteId) == nil {
			dirty.removeAll()
			controller.speak(tr("This note was deleted."))
			return false
		}
		do {
			try store.updateNote(noteId, patch())
		} catch {
			setStatus(tr("Not saved"))
			controller.speak(Messages.storeError(error, folder: store.folder))
			return false
		}
		dirty.removeAll()
		window.title = Messages.noteTitle(store.getNote(noteId))
		setStatus(tr("Saved at {time}", ["time": Messages.formatTime()]))
		if announce {
			controller.speak(tr("Note saved"))
		}
		controller.notesChanged(noteId)
		return true
	}

	/// Save and close (also Esc, Command+W and the close button): nothing is lost.
	func finish() {
		save()
		timer?.invalidate()
		endModalWindow(window)
	}

	func handleKey(_ event: NSEvent) -> Bool {
		if event.shortcutModifiers == [.command, .shift] && event.lowerChars == "f" {
			onFormatButton()
			return true
		}
		guard event.shortcutModifiers == .command else { return false }
		switch event.lowerChars {
		case "s":
			save()
			controller.speak(tr("Note saved"))
			return true
		case "b", "i":
			if window.firstResponder === contentEdit.textView {
				applyFormat(event.lowerChars == "b" ? "bold" : "italic")
				return true
			}
			return false
		default:
			return false
		}
	}

	func onFormatButton() {
		let labels = Markup.formats.map { kind -> String in
			let name = Messages.formatName(kind, applied: true)
			if let shortcut = Self.shortcuts[kind] {
				return name + "  " + shortcut
			}
			return name
		}
		if let index = Prompts.chooseFromMenu(formatButton, labels) {
			applyFormat(Markup.formats[index])
		} else {
			window.makeFirstResponder(contentEdit.textView)
		}
	}

	func applyFormat(_ kind: String) {
		let textView = contentEdit.textView
		let range = textView.selectedRange()
		let (text, start, end, applied) = Markup.applyFormat(textView.string, range.location, range.location + range.length, kind)
		// Through the text storage, so the change can be undone with Command+Z.
		let whole = NSRange(location: 0, length: (textView.string as NSString).length)
		if textView.shouldChangeText(in: whole, replacementString: text) {
			textView.textStorage?.replaceCharacters(in: whole, with: text)
			textView.didChangeText()
		}
		window.makeFirstResponder(textView)
		textView.setSelectedRange(NSRange(location: start, length: end - start))
		controller.speak(Messages.formatName(kind, applied: applied))
	}
}
