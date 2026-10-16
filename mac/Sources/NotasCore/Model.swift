// Notas Workflow Mac - Model.swift
// Data model: notes, notebooks, folders and the four lanes. Same rules as model.py of
// NotasWorkflowNVDA, so both read and write the same file.
// Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
// This file is covered by the GNU General Public License, version 2.

import Foundation

public struct Note: Equatable {
	public var id: String
	public var title: String
	public var content: String
	public var tags: [String]
	public var laneId: String
	public var notebookId: String?
	public var folderId: String?
	public var createdAt: String
	public var updatedAt: String
}

public struct Notebook: Equatable {
	public var id: String
	public var name: String
	public var color: String
	public var folderId: String?
	public var createdAt: String
}

public struct Folder: Equatable {
	public var id: String
	public var name: String
	public var color: String
	public var createdAt: String
}

/// Which notes the main window shows.
public enum NoteFilter: Hashable {
	case all
	case loose
	case recent
	case notebook(String)
	case folder(String)
}

public enum Model {
	/// The four status lanes, in order (the colours are kept in the file, never needed to use the app).
	public static let laneIds = ["todo", "inprogress", "blocked", "done"]
	public static let laneColors = ["#007AFF", "#FF9500", "#FF2D55", "#34C759"]
	public static let defaultLane = "todo"

	/// Colours given in turn to new notebooks and folders.
	public static let notebookColors = ["#007AFF", "#34C759", "#FF9500", "#FF2D55", "#AF52DE", "#5856D6"]
	public static let folderColors = ["#FF9500", "#5856D6", "#34C759", "#FF2D55", "#007AFF", "#AF52DE"]

	public static let maxTitle = 200
	public static let maxName = 100
	public static let maxTag = 50
	public static let maxTags = 30
	public static let maxContent = 1024 * 1024
	public static let maxId = 64
	/// Number of notes of "Recent notes".
	public static let recentCount = 10

	public static func newId() -> String {
		UUID().uuidString.lowercased()
	}

	public static func isValidId(_ value: Any?) -> Bool {
		guard let text = value as? String, !text.isEmpty, text.utf8.count <= maxId else { return false }
		return text.utf8.allSatisfy { c in
			(c >= 48 && c <= 57) || (c >= 65 && c <= 90) || (c >= 97 && c <= 122) || c == 45 || c == 95
		}
	}

	public static func isValidColor(_ value: Any?) -> Bool {
		guard let text = value as? String, text.utf8.count == 7, text.hasPrefix("#") else { return false }
		return text.utf8.dropFirst().allSatisfy { c in
			(c >= 48 && c <= 57) || (c >= 65 && c <= 70) || (c >= 97 && c <= 102)
		}
	}

	// MARK: dates

	private static let isoWriter: ISO8601DateFormatter = {
		let f = ISO8601DateFormatter()
		f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
		f.timeZone = TimeZone(identifier: "UTC")
		return f
	}()
	private static let isoFractional: ISO8601DateFormatter = {
		let f = ISO8601DateFormatter()
		f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
		return f
	}()
	private static let isoPlain: ISO8601DateFormatter = {
		let f = ISO8601DateFormatter()
		f.formatOptions = [.withInternetDateTime]
		return f
	}()
	private static let isoLock = NSLock()

	/// The current time as JavaScript's Date.toISOString() writes it: 2026-10-16T10:53:00.123Z
	public static func nowIso(_ now: Date = Date()) -> String {
		isoLock.lock()
		defer { isoLock.unlock() }
		return isoWriter.string(from: now)
	}

	/// Seconds since 1970 of the usual shape 2026-10-16T10:53:00.123Z (or without fractions),
	/// read by hand: 100,000 notes are checked when the file is read.
	static func fastIso(_ text: String) -> Double? {
		let b = Array(text.utf8)
		guard b.count == 24 || b.count == 20, b[4] == 45, b[7] == 45, b[10] == 84, b[13] == 58, b[16] == 58, b[b.count - 1] == 90 else { return nil }
		func num(_ from: Int, _ len: Int) -> Int? {
			var v = 0
			for i in from..<(from + len) {
				let c = b[i]
				guard c >= 48 && c <= 57 else { return nil }
				v = v * 10 + Int(c - 48)
			}
			return v
		}
		guard let y = num(0, 4), let mo = num(5, 2), let d = num(8, 2), let h = num(11, 2), let mi = num(14, 2), let s = num(17, 2),
			(1...12).contains(mo), (1...31).contains(d), h < 24, mi < 60, s < 61 else { return nil }
		var ms = 0
		if b.count == 24 {
			guard b[19] == 46, let f = num(20, 3) else { return nil }
			ms = f
		}
		// Days from the civil date (Howard Hinnant's algorithm).
		let yy = mo <= 2 ? y - 1 : y
		let era = (yy >= 0 ? yy : yy - 399) / 400
		let yoe = yy - era * 400
		let mp = (mo + 9) % 12
		let doy = (153 * mp + 2) / 5 + d - 1
		let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy
		let days = era * 146097 + doe - 719468
		return Double(days * 86400 + h * 3600 + mi * 60 + s) + Double(ms) / 1000
	}

	/// Date of an ISO text (with or without fractions, Z or offset, or without zone), or nil.
	public static func parseIso(_ value: Any?) -> Date? {
		guard var text = value as? String, !text.isEmpty, text.count <= 40 else { return nil }
		if let seconds = fastIso(text) {
			return Date(timeIntervalSince1970: seconds)
		}
		text = text.trimmingCharacters(in: .whitespaces)
		isoLock.lock()
		defer { isoLock.unlock() }
		if let d = isoFractional.date(from: text) ?? isoPlain.date(from: text) {
			return d
		}
		// Without a zone: UTC, as model.py does.
		let hasZone = text.hasSuffix("Z") || text.range(of: #"[+-]\d\d:?\d\d$"#, options: .regularExpression) != nil
		if !hasZone {
			return isoFractional.date(from: text + "Z") ?? isoPlain.date(from: text + "Z")
		}
		return nil
	}

	static func isoOr(_ value: Any?, _ fallback: String) -> String {
		if let text = value as? String, parseIso(text) != nil {
			return text
		}
		return fallback
	}

	// MARK: texts

	/// A single-line text: no control characters, trimmed and limited.
	public static func cleanText(_ value: Any?, _ limit: Int) -> String {
		guard let text = value as? String else { return "" }
		var scalars = String.UnicodeScalarView()
		for s in text.unicodeScalars {
			switch s.value {
			case 0x0D, 0x0A, 0x09:
				scalars.append(" ")
			case 0x00...0x08, 0x0B, 0x0C, 0x0E...0x1F, 0x7F:
				continue
			default:
				scalars.append(s)
			}
		}
		let trimmed = String(scalars).trimmingCharacters(in: .whitespacesAndNewlines)
		return trimmed.count > limit ? String(trimmed.prefix(limit)) : trimmed
	}

	/// Tags: text, no repetition (ignoring case), no empty one, limited.
	public static func cleanTags(_ value: Any?) -> [String] {
		var items: [Any] = []
		if let text = value as? String {
			items = text.components(separatedBy: ",")
		} else if let list = value as? [Any] {
			items = list
		} else {
			return []
		}
		var out: [String] = []
		var seen = Set<String>()
		for item in items {
			let tag = cleanText(item, maxTag)
			let key = tag.lowercased()
			if !tag.isEmpty && !seen.contains(key) {
				seen.insert(key)
				out.append(tag)
			}
			if out.count >= maxTags {
				break
			}
		}
		return out
	}

	// MARK: lanes

	public static func laneIndex(_ laneId: String) -> Int {
		laneIds.firstIndex(of: laneId) ?? 0
	}

	/// Lane before (step -1) or after (step +1), or nil at the ends.
	public static func neighbourLane(_ laneId: String, _ step: Int) -> String? {
		let i = laneIndex(laneId) + step
		return (0..<laneIds.count).contains(i) ? laneIds[i] : nil
	}

	// MARK: building and validating

	public static func makeNote(title: String, laneId: String = defaultLane, notebookId: String? = nil, folderId: String? = nil, now: Date = Date()) -> Note {
		let stamp = nowIso(now)
		return Note(
			id: newId(),
			title: cleanText(title, maxTitle),
			content: "",
			tags: [],
			laneId: laneIds.contains(laneId) ? laneId : defaultLane,
			notebookId: notebookId,
			folderId: folderId,
			createdAt: stamp,
			updatedAt: stamp
		)
	}

	public static func sanitizeFolder(_ raw: Any?, now: String) -> Folder? {
		guard let raw = raw as? [String: Any], isValidId(raw["id"]), let id = raw["id"] as? String else { return nil }
		let name = cleanText(raw["name"], maxName)
		if name.isEmpty {
			return nil
		}
		return Folder(
			id: id,
			name: name,
			color: isValidColor(raw["color"]) ? raw["color"] as! String : folderColors[0],
			createdAt: isoOr(raw["createdAt"], now)
		)
	}

	public static func sanitizeNotebook(_ raw: Any?, now: String, folderIds: Set<String>) -> Notebook? {
		guard let raw = raw as? [String: Any], isValidId(raw["id"]), let id = raw["id"] as? String else { return nil }
		let name = cleanText(raw["name"], maxName)
		if name.isEmpty {
			return nil
		}
		let folderId = raw["folderId"] as? String
		return Notebook(
			id: id,
			name: name,
			color: isValidColor(raw["color"]) ? raw["color"] as! String : notebookColors[0],
			folderId: folderId.flatMap { folderIds.contains($0) ? $0 : nil },
			createdAt: isoOr(raw["createdAt"], now)
		)
	}

	/// A valid note built from untrusted data (file or import), or nil.
	public static func sanitizeNote(_ raw: Any?, now: String, notebookIds: Set<String>, folderIds: Set<String>) -> Note? {
		guard let raw = raw as? [String: Any], isValidId(raw["id"]), let id = raw["id"] as? String else { return nil }
		var content = raw["content"] as? String ?? ""
		// utf8.count is immediate; characters are counted only for the rare long content.
		if content.utf8.count > maxContent && content.unicodeScalars.count > maxContent {
			content = ""
		}
		let lane = raw["laneId"] as? String ?? ""
		let notebookId = raw["notebookId"] as? String
		let folderId = raw["folderId"] as? String
		let created = isoOr(raw["createdAt"], now)
		return Note(
			id: id,
			title: cleanText(raw["title"], maxTitle),
			content: content,
			tags: cleanTags(raw["tags"]),
			laneId: laneIds.contains(lane) ? lane : defaultLane,
			notebookId: notebookId.flatMap { notebookIds.contains($0) ? $0 : nil },
			folderId: folderId.flatMap { folderIds.contains($0) ? $0 : nil },
			createdAt: created,
			updatedAt: isoOr(raw["updatedAt"], created)
		)
	}

	public static func updatedKey(_ note: Note) -> Double {
		fastIso(note.updatedAt) ?? parseIso(note.updatedAt)?.timeIntervalSince1970 ?? 0
	}

	/// Notes shown by a filter, in creation order (recent: last changed first).
	public static func filterNotes(_ notes: [Note], notebooks: [Notebook], filter: NoteFilter) -> [Note] {
		switch filter {
		case .loose:
			return notes.filter { $0.notebookId == nil && $0.folderId == nil }
		case .recent:
			let keyed = notes.map { ($0, updatedKey($0)) }
			return keyed.sorted { $0.1 > $1.1 }.prefix(recentCount).map { $0.0 }
		case .notebook(let id):
			return notes.filter { $0.notebookId == id }
		case .folder(let id):
			let inFolder = Set(notebooks.filter { $0.folderId == id }.map { $0.id })
			return notes.filter { $0.folderId == id || ($0.notebookId.map { inFolder.contains($0) } ?? false) }
		case .all:
			return notes
		}
	}

	/// [laneId: notes] for the four lanes, keeping the order.
	public static func byLane(_ notes: [Note]) -> [String: [Note]] {
		var out: [String: [Note]] = [:]
		for lane in laneIds {
			out[lane] = []
		}
		for note in notes {
			let lane = out[note.laneId] != nil ? note.laneId : defaultLane
			out[lane]!.append(note)
		}
		return out
	}
}
