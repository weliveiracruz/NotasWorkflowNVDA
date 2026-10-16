// Notas Workflow Mac - AppController.swift
// What the global plugin does in NotasWorkflowNVDA: owns the notes, reads them in the
// background, opens the windows, says what happened with VoiceOver and saves everything
// before the app quits.
// Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
// This file is covered by the GNU General Public License, version 2.

import AppKit
import NotasCore

enum Settings {
	static let defaults = UserDefaults.standard
	static let dataSubfolder = "NotasWorkflowMac"

	/// Chosen folder of the notes, or "" for the default one.
	static var dataFolder: String {
		get { defaults.string(forKey: "dataFolder") ?? "" }
		set { defaults.set(newValue, forKey: "dataFolder") }
	}

	static var autoSaveSeconds: Int {
		get {
			let value = defaults.integer(forKey: "autoSaveSeconds")
			return value == 0 ? 2 : max(1, min(30, value))
		}
		set { defaults.set(max(1, min(30, newValue)), forKey: "autoSaveSeconds") }
	}

	static var announceAutoSave: Bool {
		get { defaults.bool(forKey: "announceAutoSave") }
		set { defaults.set(newValue, forKey: "announceAutoSave") }
	}

	static func defaultDataFolder() -> String {
		let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
			?? URL(fileURLWithPath: NSHomeDirectory()).appendingPathComponent("Library/Application Support")
		return base.appendingPathComponent(dataSubfolder).path
	}

	static func effectiveDataFolder() -> String {
		dataFolder.isEmpty ? defaultDataFolder() : dataFolder
	}
}

final class AppController {
	static let shared = AppController()

	let store: NotesStore
	/// Prepared text of the notes for the search, kept while the notes do not change.
	let searchIndex = SearchIndex()
	/// The note window open at the moment (its changes are saved if the app quits).
	weak var openEditor: NoteWindowController?
	private(set) var loaded = false
	private var whenLoaded: [() -> Void] = []
	private var announced = false

	private init() {
		store = NotesStore(folder: Settings.effectiveDataFolder())
		store.enableBackgroundSaving { error in
			DispatchQueue.main.async {
				AppController.shared.writeFailed(error)
			}
		}
	}

	/// Reads the notes in the background (the app starts at once even with 100,000 notes),
	/// then prepares the text of the search, also in the background.
	func start() {
		let store = self.store
		DispatchQueue.global(qos: .userInitiated).async {
			store.load()
			DispatchQueue.main.async {
				self.loaded = true
				let waiting = self.whenLoaded
				self.whenLoaded = []
				self.announceAfterLoad()
				waiting.forEach { $0() }
				self.prepareSearch()
			}
		}
	}

	private func prepareSearch() {
		let notes = store.notes
		let index = searchIndex
		DispatchQueue.global(qos: .utility).async {
			for note in notes {
				_ = index.entry(note)
			}
		}
	}

	/// Runs the action when the notes are read (at once, if they already are).
	func ensureLoaded(_ action: @escaping () -> Void) {
		if loaded {
			action()
		} else {
			speak(tr("Loading the notes…"))
			whenLoaded.append(action)
		}
	}

	private func announceAfterLoad() {
		if announced {
			return
		}
		announced = true
		announceWarning()
		if store.migrated {
			speak(tr("Notes of the previous version brought to Notas Workflow NVDA: {count}. The old add-on can be uninstalled.", ["count": Messages.notesCount(store.notes.count)]))
		}
	}

	func announceWarning() {
		if case let .corrupt(savedAs, restored)? = store.warning {
			speak(Messages.corruptWarning(savedAs, restored))
			store.warning = nil
		}
	}

	/// A write in the background failed: the notes stay open and the next change tries again.
	func writeFailed(_ error: StoreError) {
		speak(Messages.storeError(error, folder: store.folder))
	}

	/// Saves everything before the app quits: the open note and the pending write.
	func terminate() {
		openEditor?.save()
		store.flush()
	}

	/// Reads the notes again when another computer changed the file. True when it did.
	@discardableResult
	func reloadIfChanged() -> Bool {
		guard loaded else { return false }
		if store.reloadIfChanged() {
			announceWarning()
			return true
		}
		return false
	}

	func changeDataFolder() {
		ensureLoaded {
			guard let result = self.safe({ try self.store.relocate(Settings.effectiveDataFolder()) }) else { return }
			self.announceWarning()
			switch result {
			case .loaded:
				self.speak(tr("Using the notes of the new folder: {count}", ["count": Messages.notesCount(self.store.notes.count)]))
			case .copied:
				self.speak(tr("Notes saved in the new folder"))
			}
			self.notesChanged()
		}
	}

	func importNotes(_ path: String) {
		ensureLoaded {
			guard let counts = self.safe({ try self.store.importFile(path) }) else { return }
			self.speak(tr("Imported: {notes}, {notebooks}, {folders} folders", [
				"notes": Messages.notesCount(counts.notes),
				"notebooks": Messages.notebooksCount(counts.notebooks),
				"folders": counts.folders,
			]))
			self.notesChanged()
		}
	}

	func exportNotes(_ path: String) {
		ensureLoaded {
			if self.safe({ try self.store.exportFile(path) }) != nil {
				self.speak(tr("Exported: {count}", ["count": Messages.notesCount(self.store.notes.count)]))
			}
		}
	}

	/// The result, or nil after saying the problem.
	func safe<T>(_ action: () throws -> T) -> T? {
		do {
			return try action()
		} catch {
			speak(Messages.storeError(error, folder: store.folder))
			return nil
		}
	}

	func speak(_ text: String) {
		Speech.say(text)
	}

	/// Called after the notes change outside the main window (editor, settings).
	func notesChanged(_ noteId: String? = nil) {
		guard let main = MainWindowController.instance else { return }
		if let noteId {
			main.noteChanged(noteId)
		} else {
			main.refresh(selectId: main.selectedNoteId())
		}
	}

	// MARK: windows

	func openWindow() {
		ensureLoaded {
			MainWindowController.open()
		}
	}

	/// New note window, then the note window. Returns the id of the new note or nil.
	@discardableResult
	func newNote(laneId: String = Model.defaultLane, notebookId: String? = nil, folderId: String? = nil) -> String? {
		guard loaded else {
			ensureLoaded { self.notesChanged(self.newNote()) }
			return nil
		}
		let dialog = NewNoteWindowController(store: store, laneId: laneId, notebookId: notebookId, folderId: folderId)
		guard let values = dialog.run(), !values.title.isEmpty else { return nil }
		guard let note = safe({ try store.addNote(title: values.title, laneId: values.laneId, notebookId: values.notebookId, folderId: values.folderId) }) else { return nil }
		speak(tr("Note created in {lane}", ["lane": Messages.laneName(note.laneId)]))
		editNote(note.id, focusContent: true)
		return note.id
	}

	/// Asks the name and creates a notebook (inside folderId).
	func createNotebook(folderId: String? = nil) -> Notebook? {
		let folder = store.getFolder(folderId)
		guard let name = Prompts.askText(Messages.askNotebookName(folder), tr("New notebook")), !name.trimmingCharacters(in: .whitespaces).isEmpty else { return nil }
		guard let notebook = safe({ try store.addNotebook(name, folderId: folderId) }) else { return nil }
		speak(Messages.notebookCreated(notebook.name))
		return notebook
	}

	/// Asks the name and creates a folder.
	func createFolder() -> Folder? {
		guard let name = Prompts.askText(tr("Name of the new folder:"), tr("New folder")), !name.trimmingCharacters(in: .whitespaces).isEmpty else { return nil }
		guard let folder = safe({ try store.addFolder(name) }) else { return nil }
		speak(Messages.folderCreated(folder.name))
		return folder
	}

	/// Move to: chooses a notebook, a folder or loose and moves the note. True when moved.
	func moveNote(_ note: Note) -> Bool {
		let (labels, places) = Messages.locationChoices(store)
		let current = Messages.placeOfNote(note)
		guard let index = Prompts.chooseItem(tr("Move {title} to:", ["title": Messages.noteTitle(note)]), tr("Move to"), labels, current: places.firstIndex(of: current) ?? 0),
			places[index] != current else { return false }
		let place = places[index]
		guard safe({ try store.moveNoteTo(note.id, notebookId: place.notebookId, folderId: place.folderId) }) != nil else { return false }
		speak(Messages.movedToPlace(labels[index]))
		return true
	}

	/// Asks and deletes a note. True when deleted.
	func deleteNote(_ note: Note) -> Bool {
		guard Prompts.confirm(tr("Delete the note {title}? This cannot be undone.", ["title": Messages.noteTitle(note)]), tr("Delete note")) else { return false }
		guard safe({ try store.deleteNote(note.id) }) != nil else { return false }
		speak(tr("Note deleted: {title}", ["title": Messages.noteTitle(note)]))
		return true
	}

	/// The note window, modal: returns when it is closed (its changes are saved).
	func editNote(_ noteId: String, focusContent: Bool = false) {
		guard store.getNote(noteId) != nil else {
			speak(Messages.storeError(StoreError(.notFound)))
			return
		}
		let editor = NoteWindowController(controller: self, noteId: noteId)
		openEditor = editor
		editor.run(focusContent: focusContent)
		openEditor = nil
	}

	/// Search window. Returns the id of the last note opened from it, or nil.
	@discardableResult
	func openSearch(query: String = "") -> String? {
		guard loaded else {
			ensureLoaded { self.openSearch() }
			return nil
		}
		let dialog = SearchWindowController(controller: self, query: query)
		dialog.run()
		return dialog.openedId
	}

	func lanesSummary() -> String {
		var counts: [String: Int] = [:]
		for (lane, notes) in Model.byLane(store.notes) {
			counts[lane] = notes.count
		}
		return Messages.lanesSummary(counts)
	}

	func sayLanesSummary() {
		ensureLoaded {
			self.reloadIfChanged()
			self.speak(self.lanesSummary())
		}
	}

	func openSettings() {
		ensureLoaded {
			SettingsWindowController(controller: self).run()
		}
	}

	// MARK: global shortcuts (NVDA+Alt+N, F and B in the add-on)

	func shortcutOpenWindow() {
		NSApp.activate(ignoringOtherApps: true)
		openWindow()
	}

	func shortcutNewNote() {
		NSApp.activate(ignoringOtherApps: true)
		ensureLoaded {
			self.notesChanged(self.newNote())
		}
	}

	func shortcutSearch() {
		NSApp.activate(ignoringOtherApps: true)
		ensureLoaded {
			if let opened = self.openSearch(), let main = MainWindowController.instance {
				main.refresh(selectId: opened)
			}
		}
	}
}
