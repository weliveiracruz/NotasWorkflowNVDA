// Notas Workflow Mac - Search.swift
// Text search of the notes, ignoring accents and case. The text of each note is prepared
// once and kept in an index until the note changes, so a search in 100,000 notes takes a
// fraction of a second. Port of search.py.
// Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
// This file is covered by the GNU General Public License, version 2.

import Foundation
#if canImport(Darwin)
import Darwin
#else
import Glibc
#endif

public struct SearchResult {
	public let note: Note
	public let score: Double
	public let excerpt: String
}

public enum Search {
	public static let maxResults = 100
	public static let excerptLength = 120
	public static let maxQuery = 200

	static let skipRe = Rx("<(script|style|template|noscript|iframe|object|head|title)\\b[^>]*>.*?</\\1\\s*>", [.caseInsensitive, .dotMatchesLineSeparators])
	static let tagRe = Rx("<[^>]*>")
	static let spacesRe = Rx("\\s+")

	/// Lower case without accents: "Ação" -> "acao".
	public static func fold(_ text: String) -> String {
		text.folding(options: [.diacriticInsensitive, .widthInsensitive], locale: nil).lowercased()
	}

	/// Words of the stored HTML for the search: tags, scripts and styles removed.
	public static func plainText(_ content: String) -> String {
		if content.isEmpty {
			return ""
		}
		var text = content
		if text.contains("<") {
			text = tagRe.replace(skipRe.replace(text, " "), " ")
		}
		return spacesRe.replace(HTMLEntities.unescape(text), " ").trimmingCharacters(in: .whitespacesAndNewlines)
	}

	public static func terms(_ query: String) -> [String] {
		fold(String(query.prefix(maxQuery))).split(whereSeparator: { $0.isWhitespace }).map(String.init)
	}

	/// Part of the text around the first term found.
	public static func excerpt(_ plainIn: String, _ query: String, maxLen: Int = excerptLength) -> String {
		let plain = plainIn.split(whereSeparator: { $0.isWhitespace }).joined(separator: " ")
		let chars = Array(plain)
		func head() -> String {
			String(chars.prefix(maxLen)) + (chars.count > maxLen ? "…" : "")
		}
		let found = terms(query)
		if found.isEmpty {
			return head()
		}
		var idx: Int?
		let folded = fold(plain)
		if folded.count == chars.count {
			// Each character became one character (the usual case): same positions.
			for t in found {
				if let r = folded.range(of: t, options: .literal) {
					idx = folded.distance(from: folded.startIndex, to: r.lowerBound)
					break
				}
			}
		} else {
			var bytes: [UInt8] = []
			var positions: [Int] = []
			for (i, ch) in chars.enumerated() {
				let f = Array(fold(String(ch)).utf8)
				bytes.append(contentsOf: f)
				positions.append(contentsOf: repeatElement(i, count: f.count))
			}
			for t in found {
				if let at = find(Array(t.utf8), in: bytes) {
					idx = positions[at]
					break
				}
			}
		}
		guard let i = idx else { return head() }
		let start = max(0, i - 40)
		let end = min(chars.count, i + maxLen - 40)
		return (start > 0 ? "…" : "") + String(chars[start..<max(start, end)]) + (end < chars.count ? "…" : "")
	}

	/// Byte offset of needle in haystack, or nil.
	static func find(_ needle: [UInt8], in haystack: [UInt8]) -> Int? {
		if needle.isEmpty {
			return 0
		}
		if needle.count > haystack.count {
			return nil
		}
		return haystack.withUnsafeBytes { (h: UnsafeRawBufferPointer) -> Int? in
			needle.withUnsafeBytes { (n: UnsafeRawBufferPointer) -> Int? in
				guard let base = h.baseAddress, let nb = n.baseAddress, let p = memmem(base, h.count, nb, n.count) else { return nil }
				return base.distance(to: UnsafeRawPointer(p))
			}
		}
	}

	/// [(note, score, excerpt)] best first. score = terms found / terms; ties: more terms in
	/// the title, then the note changed last.
	public static func search(_ notes: [Note], _ query: String, limit: Int = maxResults, index: SearchIndex? = nil) -> [SearchResult] {
		let wanted = terms(query)
		if wanted.isEmpty {
			return []
		}
		let wantedBytes = wanted.map { Array($0.utf8) }
		let index = index ?? SearchIndex()
		var ranked: [(Double, Int, Double, Int, SearchIndex.Entry)] = []
		for (position, note) in notes.enumerated() {
			let entry = index.entry(note)
			var hits = 0
			for t in wantedBytes where find(t, in: entry.haystack) != nil {
				hits += 1
			}
			if hits == 0 {
				continue
			}
			var titleHits = 0
			for t in wantedBytes where find(t, in: entry.foldedTitle) != nil {
				titleHits += 1
			}
			ranked.append((Double(hits) / Double(wanted.count), titleHits, entry.updated, position, entry))
		}
		// Only the best ones are ordered (a common word can match tens of thousands of notes).
		ranked.sort { a, b in
			if a.0 != b.0 { return a.0 > b.0 }
			if a.1 != b.1 { return a.1 > b.1 }
			if a.2 != b.2 { return a.2 > b.2 }
			return a.3 < b.3
		}
		return ranked.prefix(limit).map { r in
			SearchResult(note: notes[r.3], score: r.0, excerpt: excerpt(r.4.plain, query))
		}
	}
}

/// Prepared text of each note (plain text, folded title and folded haystack). An entry is
/// rebuilt only when the note changes. Safe to fill from a background queue.
public final class SearchIndex {
	public final class Entry {
		let updatedAt: String
		let title: String
		let contentSize: Int
		let tags: [String]
		let plain: String
		let foldedTitle: [UInt8]
		let haystack: [UInt8]
		let updated: Double

		init(_ note: Note) {
			updatedAt = note.updatedAt
			title = note.title
			contentSize = note.content.utf8.count
			tags = note.tags
			plain = Search.plainText(note.content)
			let ft = Search.fold(note.title)
			foldedTitle = Array(ft.utf8)
			haystack = Array([ft, Search.fold(plain), Search.fold(note.tags.joined(separator: " "))].joined(separator: " ").utf8)
			updated = Model.updatedKey(note)
		}

		func matches(_ note: Note) -> Bool {
			updatedAt == note.updatedAt && title == note.title && contentSize == note.content.utf8.count && tags == note.tags
		}
	}

	private var entries: [String: Entry] = [:]
	private let lock = NSLock()

	public init() {}

	public func entry(_ note: Note) -> Entry {
		lock.lock()
		let cached = entries[note.id]
		lock.unlock()
		if let cached, cached.matches(note) {
			return cached
		}
		let fresh = Entry(note)
		lock.lock()
		entries[note.id] = fresh
		lock.unlock()
		return fresh
	}

	/// Drops the entries of notes that no longer exist.
	public func forget(keep: Set<String>) {
		lock.lock()
		entries = entries.filter { keep.contains($0.key) }
		lock.unlock()
	}

	public var count: Int {
		lock.lock()
		defer { lock.unlock() }
		return entries.count
	}
}
