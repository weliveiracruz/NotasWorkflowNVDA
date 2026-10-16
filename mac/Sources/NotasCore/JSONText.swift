// Notas Workflow Mac - JSONText.swift
// Compact JSON of the data file, written by hand: the keys keep the same order as the
// file written by NotasWorkflowNVDA, and 100,000 notes are encoded in a fraction of a second.
// Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
// This file is covered by the GNU General Public License, version 2.

import Foundation

struct JSONText {
	private(set) var bytes: [UInt8] = []

	init(capacity: Int = 0) {
		bytes.reserveCapacity(capacity)
	}

	mutating func raw(_ text: StaticString) {
		text.withUTF8Buffer { bytes.append(contentsOf: $0) }
	}

	mutating func number(_ value: Int) {
		bytes.append(contentsOf: Array(String(value).utf8))
	}

	/// A JSON string as Python's json writes it with ensure_ascii=False.
	mutating func string(_ value: String) {
		bytes.append(34)
		for c in value.utf8 {
			switch c {
			case 34:
				bytes.append(92); bytes.append(34)
			case 92:
				bytes.append(92); bytes.append(92)
			case 10:
				bytes.append(92); bytes.append(110)
			case 13:
				bytes.append(92); bytes.append(114)
			case 9:
				bytes.append(92); bytes.append(116)
			case 8:
				bytes.append(92); bytes.append(98)
			case 12:
				bytes.append(92); bytes.append(102)
			case 0..<32:
				let hex = Array("0123456789abcdef".utf8)
				bytes.append(contentsOf: [92, 117, 48, 48, hex[Int(c >> 4)], hex[Int(c & 15)]])
			default:
				bytes.append(c)
			}
		}
		bytes.append(34)
	}

	mutating func optionalString(_ value: String?) {
		if let value {
			string(value)
		} else {
			raw("null")
		}
	}

	mutating func folder(_ f: Folder) {
		raw("{\"id\":"); string(f.id)
		raw(",\"name\":"); string(f.name)
		raw(",\"color\":"); string(f.color)
		raw(",\"createdAt\":"); string(f.createdAt)
		raw("}")
	}

	mutating func notebook(_ nb: Notebook) {
		raw("{\"id\":"); string(nb.id)
		raw(",\"name\":"); string(nb.name)
		raw(",\"color\":"); string(nb.color)
		raw(",\"folderId\":"); optionalString(nb.folderId)
		raw(",\"createdAt\":"); string(nb.createdAt)
		raw("}")
	}

	mutating func note(_ n: Note) {
		raw("{\"id\":"); string(n.id)
		raw(",\"title\":"); string(n.title)
		raw(",\"content\":"); string(n.content)
		raw(",\"tags\":[")
		for (i, tag) in n.tags.enumerated() {
			if i > 0 { raw(",") }
			string(tag)
		}
		raw("],\"laneId\":"); string(n.laneId)
		raw(",\"notebookId\":"); optionalString(n.notebookId)
		raw(",\"folderId\":"); optionalString(n.folderId)
		raw(",\"createdAt\":"); string(n.createdAt)
		raw(",\"updatedAt\":"); string(n.updatedAt)
		raw("}")
	}

	/// The whole data file.
	static func encode(_ data: StoreSnapshot) -> Data {
		var out = JSONText(capacity: 1024 + data.notes.count * 400)
		out.raw("{\"format\":"); out.string(NotesStore.format)
		out.raw(",\"version\":"); out.number(NotesStore.version)
		out.raw(",\"folders\":[")
		for (i, f) in data.folders.enumerated() {
			if i > 0 { out.raw(",") }
			out.folder(f)
		}
		out.raw("],\"notebooks\":[")
		for (i, nb) in data.notebooks.enumerated() {
			if i > 0 { out.raw(",") }
			out.notebook(nb)
		}
		out.raw("],\"notes\":[")
		for (i, n) in data.notes.enumerated() {
			if i > 0 { out.raw(",") }
			out.note(n)
		}
		out.raw("]}")
		return Data(out.bytes)
	}
}
