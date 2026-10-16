// Notas Workflow Mac - Store.swift
// The operations on notes, notebooks and folders and their persistence in a JSON file
// written atomically with a backup copy. Same file as NotasWorkflowNVDA
// (NotasWorkflowNVDA-data.json), so a synced folder can serve Windows and Mac.
// Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
// This file is covered by the GNU General Public License, version 2.

import Foundation
#if canImport(Darwin)
import Darwin
#else
import Glibc
#endif

public enum StoreErrorKind: String {
	case write, corrupt, tooLarge, invalidImport, notFound, emptyName
}

public struct StoreError: Error, Equatable {
	public let kind: StoreErrorKind
	public let detail: String

	public init(_ kind: StoreErrorKind, _ detail: String = "") {
		self.kind = kind
		self.detail = String(detail.prefix(200))
	}
}

/// What is written: copies of the lists (Swift arrays are values, so a write in the
/// background is not disturbed by notes changed meanwhile).
public struct StoreSnapshot {
	public var folders: [Folder]
	public var notebooks: [Notebook]
	public var notes: [Note]
}

/// The fields of a note to change. notebookId and folderId: .some(nil) puts the note out of them.
public struct NotePatch {
	public var title: String?
	public var content: String?
	public var tags: [String]?
	public var laneId: String?
	public var notebookId: String??
	public var folderId: String??

	public init(title: String? = nil, content: String? = nil, tags: [String]? = nil, laneId: String? = nil, notebookId: String?? = nil, folderId: String?? = nil) {
		self.title = title
		self.content = content
		self.tags = tags
		self.laneId = laneId
		self.notebookId = notebookId
		self.folderId = folderId
	}
}

public enum LoadWarning: Equatable {
	/// The file was damaged: kept with the name savedAs; restored when the backup copy was used.
	case corrupt(savedAs: String, restored: Bool)
}

func readJSON(_ path: String) throws -> Any {
	let attrs = try FileManager.default.attributesOfItem(atPath: path)
	let size = (attrs[.size] as? NSNumber)?.intValue ?? 0
	if size > NotesStore.maxFileSize {
		throw StoreError(.tooLarge)
	}
	var data = try Data(contentsOf: URL(fileURLWithPath: path))
	if data.count > NotesStore.maxFileSize {
		throw StoreError(.tooLarge)
	}
	if data.starts(with: [0xEF, 0xBB, 0xBF]) {
		data = data.dropFirst(3)
	}
	return try JSONSerialization.jsonObject(with: data, options: [.fragmentsAllowed])
}

struct InvalidData: Error {
	let reason: String
}

/// (folders, notebooks, notes) validated from data of Notas Workflow (this app, the NVDA
/// add-on or the web app). Accepts {"folders", "notebooks", "notes"}, the keys of older
/// exports ("notas-workflow:notes"...) or just a list of notes.
public func parseData(_ input: Any, now: String = Model.nowIso()) throws -> ([Folder], [Notebook], [Note]) {
	var data: [String: Any]
	if let list = input as? [Any] {
		data = ["notes": list]
	} else if let dict = input as? [String: Any] {
		data = dict
	} else {
		throw InvalidData(reason: "not an object")
	}
	for key in ["notes", "notebooks", "folders"] where data[key] == nil {
		if var value = data[NotesStore.webPrefix + key] {
			if let text = value as? String {
				// localStorage keeps the arrays as JSON text.
				value = try JSONSerialization.jsonObject(with: Data(text.utf8), options: [.fragmentsAllowed])
			}
			data[key] = value
		}
	}
	if let byId = data["notes"] as? [String: Any] {
		// Some exports keep the notes as {id: note}.
		data["notes"] = Array(byId.values)
	}
	if !["notes", "notebooks", "folders"].contains(where: { data[$0] is [Any] }) {
		throw InvalidData(reason: "no notes")
	}
	let folders = unique((data["folders"] as? [Any] ?? []).compactMap { Model.sanitizeFolder($0, now: now) }, \.id)
	let folderIds = Set(folders.map(\.id))
	let notebooks = unique((data["notebooks"] as? [Any] ?? []).compactMap { Model.sanitizeNotebook($0, now: now, folderIds: folderIds) }, \.id)
	let notebookIds = Set(notebooks.map(\.id))
	let notes = unique((data["notes"] as? [Any] ?? []).compactMap { Model.sanitizeNote($0, now: now, notebookIds: notebookIds, folderIds: folderIds) }, \.id)
	return (folders, notebooks, notes)
}

func unique<T>(_ items: [T], _ key: KeyPath<T, String>) -> [T] {
	var seen = Set<String>()
	var out: [T] = []
	out.reserveCapacity(items.count)
	for item in items where seen.insert(item[keyPath: key]).inserted {
		out.append(item)
	}
	return out
}

/// Writes the file on a background queue. Changes made in a row become a single write
/// (only the latest state is written), half a second after the last one.
final class BackgroundWriter {
	private let queue = DispatchQueue(label: "NotasWorkflowMac.save", qos: .utility)
	private let lock = NSLock()
	private var pending: (StoreSnapshot, String)?
	private var generation = 0
	private var writing = false
	private(set) var lastError: StoreError?
	private let onError: ((StoreError) -> Void)?
	private let write: (StoreSnapshot, String) throws -> Void

	init(onError: ((StoreError) -> Void)?, write: @escaping (StoreSnapshot, String) throws -> Void) {
		self.onError = onError
		self.write = write
	}

	func request(_ data: StoreSnapshot, path: String) {
		lock.lock()
		pending = (data, path)
		generation += 1
		let mine = generation
		lock.unlock()
		queue.asyncAfter(deadline: .now() + NotesStore.writeDelay) { [weak self] in
			guard let self else { return }
			self.lock.lock()
			guard mine == self.generation, let job = self.pending else {
				self.lock.unlock()
				return
			}
			self.pending = nil
			self.writing = true
			self.lock.unlock()
			self.run(job)
		}
	}

	private func run(_ job: (StoreSnapshot, String)) {
		do {
			try write(job.0, job.1)
			lock.lock(); lastError = nil; writing = false; lock.unlock()
		} catch {
			let e = error as? StoreError ?? StoreError(.write, String(describing: type(of: error)))
			lock.lock(); lastError = e; writing = false; lock.unlock()
			onError?(e)
		}
	}

	var busy: Bool {
		lock.lock()
		defer { lock.unlock() }
		return pending != nil || writing
	}

	/// Writes what is pending now and waits. Returns the error of a failed write, or nil.
	@discardableResult
	func flush() -> StoreError? {
		lock.lock()
		let job = pending
		pending = nil
		generation += 1
		if job != nil {
			writing = true
		}
		lock.unlock()
		queue.sync {
			if let job {
				self.run(job)
			}
		}
		lock.lock()
		let error = lastError
		lastError = nil
		lock.unlock()
		return error
	}
}

public final class NotesStore {
	public static let fileName = "NotasWorkflowNVDA-data.json"
	/// Name of the data file up to NotasWorkflow 1.0.0 (NVDA add-on).
	public static let legacyFileName = "NotasWorkflow-data.json"
	public static let format = "notas-workflow"
	public static let version = 1
	/// Data and import files above this size are refused without being read.
	public static let maxFileSize = 200 * 1024 * 1024
	/// The background write waits this long after the last change.
	public static let writeDelay = 0.5
	/// Keys of older exports (browser storage), still accepted on import.
	public static let webPrefix = "notas-workflow:"

	public var folder: String
	public private(set) var folders: [Folder] = []
	public private(set) var notebooks: [Notebook] = []
	public private(set) var notes: [Note] = [] {
		didSet { indexValid = false }
	}
	private var index: [String: Int] = [:]
	private var indexValid = false
	private var stamp: [Double]?
	/// The last problem found while loading, for the interface.
	public var warning: LoadWarning?
	/// True when the last load copied a data file of NotasWorkflow 1.0.0.
	public private(set) var migrated = false
	private var writer: BackgroundWriter?

	public init(folder: String) {
		self.folder = folder
	}

	public var path: String { (folder as NSString).appendingPathComponent(Self.fileName) }
	public var backupPath: String { path + ".bak" }

	// MARK: file

	private func fileStamp() -> [Double]? {
		guard let attrs = try? FileManager.default.attributesOfItem(atPath: path) else { return nil }
		let size = (attrs[.size] as? NSNumber)?.doubleValue ?? -1
		let date = (attrs[.modificationDate] as? Date)?.timeIntervalSince1970 ?? -1
		return [size, date]
	}

	/// Copies the data file of NotasWorkflow 1.0.0 of this folder to the new name when there is
	/// no file with the new name yet. The old file is never moved or deleted.
	func adoptLegacyFile() -> Bool {
		let fm = FileManager.default
		let legacy = (folder as NSString).appendingPathComponent(Self.legacyFileName)
		if fm.fileExists(atPath: path) || !fm.fileExists(atPath: legacy) {
			return false
		}
		return (try? fm.copyItem(atPath: legacy, toPath: path)) != nil
	}

	/// Reads the file. A damaged file is kept with another name and the backup copy is used.
	public func load() {
		flush()
		migrated = adoptLegacyFile()
		warning = nil
		apply(([], [], []))
		guard FileManager.default.fileExists(atPath: path) else {
			stamp = nil
			return
		}
		do {
			apply(try parseData(try readJSON(path)))
		} catch {
			let saved = keepDamaged()
			var restored = false
			if FileManager.default.fileExists(atPath: backupPath), let parsed = try? parseData(try readJSON(backupPath)) {
				apply(parsed)
				restored = true
			} else {
				apply(([], [], []))
			}
			warning = .corrupt(savedAs: saved.map { ($0 as NSString).lastPathComponent } ?? "", restored: restored)
			if restored {
				try? save()
			}
			return
		}
		stamp = fileStamp()
	}

	private func apply(_ parsed: ([Folder], [Notebook], [Note])) {
		folders = parsed.0
		notebooks = parsed.1
		notes = parsed.2
	}

	private func keepDamaged() -> String? {
		let f = DateFormatter()
		f.dateFormat = "yyyyMMdd-HHmmss"
		f.locale = Locale(identifier: "en_US_POSIX")
		let target = (folder as NSString).appendingPathComponent("NotasWorkflowNVDA-data.corrupt-\(f.string(from: Date())).json")
		return rename(path, target) == 0 ? target : nil
	}

	public func snapshot() -> StoreSnapshot {
		StoreSnapshot(folders: folders, notebooks: notebooks, notes: notes)
	}

	/// From now on save() returns at once and a background queue writes the file.
	/// onError is called on that queue. flush() waits for the write: call it before quitting.
	public func enableBackgroundSaving(onError: ((StoreError) -> Void)? = nil) {
		if writer == nil {
			writer = BackgroundWriter(onError: onError) { [weak self] data, path in
				guard let self else { return }
				try self.write(data, to: path)
			}
		}
	}

	/// Waits for the background write, if any. Returns the error of a failed write, or nil.
	@discardableResult
	public func flush() -> StoreError? {
		writer?.flush()
	}

	public func save() throws {
		if let writer {
			writer.request(snapshot(), path: path)
			return
		}
		try write(snapshot(), to: path)
	}

	/// Atomic write: temporary file, backup of the previous file, rename.
	func write(_ data: StoreSnapshot, to target: String) throws {
		let dir = (target as NSString).deletingLastPathComponent
		let tmp = target + ".tmp"
		do {
			try FileManager.default.createDirectory(atPath: dir, withIntermediateDirectories: true)
			let bytes = JSONText.encode(data)
			FileManager.default.createFile(atPath: tmp, contents: nil)
			guard let handle = FileHandle(forWritingAtPath: tmp) else {
				throw StoreError(.write, "open")
			}
			do {
				try handle.write(contentsOf: bytes)
				try handle.synchronize()
				try handle.close()
			} catch {
				try? handle.close()
				throw error
			}
			if FileManager.default.fileExists(atPath: target) {
				_ = rename(target, target + ".bak")
			}
			if rename(tmp, target) != 0 {
				throw StoreError(.write, "rename")
			}
		} catch {
			try? FileManager.default.removeItem(atPath: tmp)
			if let e = error as? StoreError {
				throw e
			}
			throw StoreError(.write, String(describing: type(of: error)))
		}
		if target == path {
			let newStamp = fileStamp()
			if Thread.isMainThread {
				stamp = newStamp
			} else {
				DispatchQueue.main.async { [weak self] in
					if self?.path == target {
						self?.stamp = newStamp
					}
				}
			}
		}
	}

	public func changedOnDisk() -> Bool {
		if writer?.busy == true {
			// Our own write is running: the file is not someone else's.
			return false
		}
		return fileStamp() != stamp
	}

	/// Reads the file again when another program (a synced folder) changed it.
	@discardableResult
	public func reloadIfChanged() -> Bool {
		if changedOnDisk() {
			load()
			return true
		}
		return false
	}

	public enum RelocateResult {
		case loaded, copied
	}

	/// Uses another folder: its notes when it has them, otherwise the current notes are written there.
	public func relocate(_ newFolder: String) throws -> RelocateResult {
		flush()
		let old = folder
		folder = newFolder
		if FileManager.default.fileExists(atPath: path) {
			load()
			return .loaded
		}
		do {
			try write(snapshot(), to: path)
			stamp = fileStamp()
		} catch {
			folder = old
			throw error
		}
		return .copied
	}

	// MARK: import and export

	/// Joins the notes of an exported file. Same id: the one changed last wins.
	/// Returns what was added or updated.
	public func importFile(_ importPath: String) throws -> (notes: Int, notebooks: Int, folders: Int) {
		let parsed: ([Folder], [Notebook], [Note])
		do {
			parsed = try parseData(try readJSON(importPath))
		} catch let e as StoreError where e.kind == .tooLarge {
			throw e
		} catch {
			throw StoreError(.invalidImport, String(describing: type(of: error)))
		}
		var counts = (notes: 0, notebooks: 0, folders: 0)
		var known = Set(folders.map(\.id))
		for f in parsed.0 where !known.contains(f.id) {
			folders.append(f)
			counts.folders += 1
		}
		known = Set(notebooks.map(\.id))
		for nb in parsed.1 where !known.contains(nb.id) {
			notebooks.append(nb)
			counts.notebooks += 1
		}
		var all = notes
		var positions: [String: Int] = [:]
		for (i, n) in all.enumerated() {
			positions[n.id] = i
		}
		for note in parsed.2 {
			if let i = positions[note.id] {
				if Model.updatedKey(note) > Model.updatedKey(all[i]) {
					all[i] = note
					counts.notes += 1
				}
			} else {
				positions[note.id] = all.count
				all.append(note)
				counts.notes += 1
			}
		}
		notes = all
		if counts.notes + counts.notebooks + counts.folders > 0 {
			try save()
		}
		return counts
	}

	public func exportFile(_ exportPath: String) throws {
		do {
			try JSONText.encode(snapshot()).write(to: URL(fileURLWithPath: exportPath))
		} catch {
			throw StoreError(.write, String(describing: type(of: error)))
		}
	}

	// MARK: reading

	private func position(_ noteId: String) -> Int? {
		if !indexValid {
			index = [:]
			index.reserveCapacity(notes.count)
			for (i, n) in notes.enumerated() {
				index[n.id] = i
			}
			indexValid = true
		}
		return index[noteId]
	}

	/// O(1) with an index by id.
	public func getNote(_ noteId: String?) -> Note? {
		guard let noteId, let i = position(noteId) else { return nil }
		return notes[i]
	}

	public func getNotebook(_ notebookId: String?) -> Notebook? {
		guard let notebookId else { return nil }
		return notebooks.first { $0.id == notebookId }
	}

	public func getFolder(_ folderId: String?) -> Folder? {
		guard let folderId else { return nil }
		return folders.first { $0.id == folderId }
	}

	public func notebookName(_ notebookId: String?) -> String {
		getNotebook(notebookId)?.name ?? ""
	}

	public func filtered(_ filter: NoteFilter) -> [Note] {
		Model.filterNotes(notes, notebooks: notebooks, filter: filter)
	}

	public func notebooksIn(_ folderId: String?) -> [Notebook] {
		notebooks.filter { $0.folderId == folderId }
	}

	public func notesIn(_ notebookId: String) -> [Note] {
		notes.filter { $0.notebookId == notebookId }
	}

	/// Notes put directly in a folder (not in one of its notebooks).
	public func notesInFolder(_ folderId: String) -> [Note] {
		notes.filter { $0.folderId == folderId && $0.notebookId == nil }
	}

	public func looseNotes() -> [Note] {
		notes.filter { $0.notebookId == nil && $0.folderId == nil }
	}

	/// Numbers of notes by place in one pass: (by notebook, directly by folder, loose).
	public func placeCounts() -> (byNotebook: [String: Int], byFolder: [String: Int], loose: Int) {
		var byNotebook: [String: Int] = [:]
		var byFolder: [String: Int] = [:]
		var loose = 0
		for n in notes {
			if let nb = n.notebookId {
				byNotebook[nb, default: 0] += 1
			} else if let f = n.folderId {
				byFolder[f, default: 0] += 1
			} else {
				loose += 1
			}
		}
		return (byNotebook, byFolder, loose)
	}

	// MARK: notes

	/// Valid (notebookId, folderId) of a note: a notebook, a folder directly, or neither (loose).
	public func location(notebookId: String?, folderId: String?) -> (String?, String?) {
		if let nb = notebookId, getNotebook(nb) != nil {
			return (nb, nil)
		}
		if let f = folderId, getFolder(f) != nil {
			return (nil, f)
		}
		return (nil, nil)
	}

	@discardableResult
	public func addNote(title: String, laneId: String = Model.defaultLane, notebookId: String? = nil, folderId: String? = nil) throws -> Note {
		let (nb, f) = location(notebookId: notebookId, folderId: folderId)
		let note = Model.makeNote(title: title, laneId: laneId, notebookId: nb, folderId: f)
		let wasValid = indexValid
		notes.append(note)
		if wasValid {
			index[note.id] = notes.count - 1
			indexValid = true
		}
		try save()
		return note
	}

	/// Changes the given fields; updatedAt only changes when something really changed.
	/// Returns true when the note changed.
	@discardableResult
	public func updateNote(_ noteId: String, _ patch: NotePatch) throws -> Bool {
		guard let i = position(noteId) else { throw StoreError(.notFound, "note") }
		var note = notes[i]
		let before = note
		if let title = patch.title {
			note.title = Model.cleanText(title, Model.maxTitle)
		}
		if let content = patch.content {
			note.content = content.unicodeScalars.count > Model.maxContent ? String(String.UnicodeScalarView(content.unicodeScalars.prefix(Model.maxContent))) : content
		}
		if let tags = patch.tags {
			note.tags = Model.cleanTags(tags)
		}
		if let lane = patch.laneId, Model.laneIds.contains(lane) {
			note.laneId = lane
		}
		if let nb = patch.notebookId {
			note.notebookId = nb.flatMap { getNotebook($0) != nil ? $0 : nil }
		}
		if let f = patch.folderId {
			note.folderId = f.flatMap { getFolder($0) != nil ? $0 : nil }
		}
		if note == before {
			return false
		}
		note.updatedAt = Model.nowIso()
		// Replacing an item keeps the positions: the index stays valid.
		let wasValid = indexValid
		notes[i] = note
		indexValid = wasValid
		try save()
		return true
	}

	public func deleteNote(_ noteId: String) throws {
		guard let i = position(noteId) else { throw StoreError(.notFound, "note") }
		notes.remove(at: i)
		try save()
	}

	@discardableResult
	public func moveNote(_ noteId: String, laneId: String) throws -> Bool {
		try updateNote(noteId, NotePatch(laneId: laneId))
	}

	/// Moves the note to a notebook, to a folder or out of both. True when it changed.
	@discardableResult
	public func moveNoteTo(_ noteId: String, notebookId: String?, folderId: String?) throws -> Bool {
		let (nb, f) = location(notebookId: notebookId, folderId: folderId)
		return try updateNote(noteId, NotePatch(notebookId: .some(nb), folderId: .some(f)))
	}

	// MARK: folders

	@discardableResult
	public func addFolder(_ name: String) throws -> Folder {
		let clean = Model.cleanText(name, Model.maxName)
		if clean.isEmpty {
			throw StoreError(.emptyName)
		}
		let folder = Folder(id: Model.newId(), name: clean, color: Model.folderColors[folders.count % Model.folderColors.count], createdAt: Model.nowIso())
		folders.append(folder)
		try save()
		return folder
	}

	public func renameFolder(_ folderId: String, _ name: String) throws {
		guard let i = folders.firstIndex(where: { $0.id == folderId }) else { throw StoreError(.notFound, "folder") }
		let clean = Model.cleanText(name, Model.maxName)
		if clean.isEmpty {
			throw StoreError(.emptyName)
		}
		folders[i].name = clean
		try save()
	}

	/// Notebooks and notes of the folder become loose (nothing is deleted).
	public func deleteFolder(_ folderId: String) throws {
		guard let i = folders.firstIndex(where: { $0.id == folderId }) else { throw StoreError(.notFound, "folder") }
		folders.remove(at: i)
		for j in notebooks.indices where notebooks[j].folderId == folderId {
			notebooks[j].folderId = nil
		}
		let wasValid = indexValid
		for j in notes.indices where notes[j].folderId == folderId {
			notes[j].folderId = nil
		}
		indexValid = wasValid
		try save()
	}

	// MARK: notebooks

	@discardableResult
	public func addNotebook(_ name: String, folderId: String? = nil) throws -> Notebook {
		let clean = Model.cleanText(name, Model.maxName)
		if clean.isEmpty {
			throw StoreError(.emptyName)
		}
		let folder = folderId.flatMap { getFolder($0) != nil ? $0 : nil }
		let notebook = Notebook(id: Model.newId(), name: clean, color: Model.notebookColors[notebooks.count % Model.notebookColors.count], folderId: folder, createdAt: Model.nowIso())
		notebooks.append(notebook)
		try save()
		return notebook
	}

	public func renameNotebook(_ notebookId: String, _ name: String) throws {
		guard let i = notebooks.firstIndex(where: { $0.id == notebookId }) else { throw StoreError(.notFound, "notebook") }
		let clean = Model.cleanText(name, Model.maxName)
		if clean.isEmpty {
			throw StoreError(.emptyName)
		}
		notebooks[i].name = clean
		try save()
	}

	public func moveNotebookToFolder(_ notebookId: String, _ folderId: String?) throws {
		guard let i = notebooks.firstIndex(where: { $0.id == notebookId }) else { throw StoreError(.notFound, "notebook") }
		if let folderId, getFolder(folderId) == nil {
			throw StoreError(.notFound, "folder")
		}
		notebooks[i].folderId = folderId
		try save()
	}

	/// The notes of the notebook become loose (nothing is deleted).
	public func deleteNotebook(_ notebookId: String) throws {
		guard let i = notebooks.firstIndex(where: { $0.id == notebookId }) else { throw StoreError(.notFound, "notebook") }
		notebooks.remove(at: i)
		let wasValid = indexValid
		for j in notes.indices where notes[j].notebookId == notebookId {
			notes[j].notebookId = nil
		}
		indexValid = wasValid
		try save()
	}
}
