// Notas Workflow Mac - Messages.swift
// Translated texts shared by the windows and the commands (port of messages.py).
// Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
// This file is covered by the GNU General Public License, version 2.

import Foundation
import NotasCore

/// The text in the language of the Mac (Portuguese or English). Keys are the English texts
/// of NotasWorkflowNVDA, with & before the access letter as in the add-on.
func tr(_ text: String) -> String {
	Translations.current[text] ?? text
}

/// Translated text with {name} fields filled.
func tr(_ text: String, _ fields: [String: Any]) -> String {
	var out = tr(text)
	for (key, value) in fields {
		out = out.replacingOccurrences(of: "{\(key)}", with: "\(value)")
	}
	return out
}

/// A label without the & of the access letter (macOS has no access letters).
func plainLabel(_ text: String) -> String {
	var out = ""
	var chars = Array(text)[...]
	while let c = chars.popFirst() {
		if c == "&" {
			if chars.first == "&" {
				out.append("&")
				chars = chars.dropFirst()
			}
			continue
		}
		out.append(c)
	}
	return out
}

/// Translated label without the access letter.
func ui(_ text: String) -> String {
	plainLabel(tr(text))
}

func ui(_ text: String, _ fields: [String: Any]) -> String {
	plainLabel(tr(text, fields))
}

enum Messages {
	static let appName = "Notas Workflow Mac"

	static func laneName(_ laneId: String) -> String {
		switch laneId {
		case "inprogress": return tr("In progress")
		case "blocked": return tr("Blocked")
		case "done": return tr("Done")
		default: return tr("To do")
		}
	}

	static func laneNames() -> [String] {
		Model.laneIds.map(laneName)
	}

	static func untitled() -> String {
		tr("Untitled")
	}

	static func noteTitle(_ note: Note?) -> String {
		guard let note, !note.title.isEmpty else { return untitled() }
		return note.title
	}

	static func notesCount(_ count: Int) -> String {
		count == 1 ? tr("1 note") : tr("{count} notes", ["count": count])
	}

	static func notebooksCount(_ count: Int) -> String {
		count == 1 ? tr("1 notebook") : tr("{count} notebooks", ["count": count])
	}

	static func looseNote() -> String {
		tr("Loose note (no notebook or folder)")
	}

	static func notebookPlace(_ notebook: Notebook, _ folder: Folder? = nil) -> String {
		if let folder {
			return tr("Notebook {name} (folder {folder})", ["name": notebook.name, "folder": folder.name])
		}
		return tr("Notebook {name}", ["name": notebook.name])
	}

	static func folderPlace(_ folder: Folder) -> String {
		tr("Folder {name}", ["name": folder.name])
	}

	struct Place: Equatable {
		let notebookId: String?
		let folderId: String?
	}

	/// (labels, places) of every place a note can be: loose, each folder followed by its
	/// notebooks, then the notebooks without folder.
	static func locationChoices(_ store: NotesStore) -> ([String], [Place]) {
		var labels = [looseNote()]
		var places = [Place(notebookId: nil, folderId: nil)]
		for folder in store.folders {
			labels.append(folderPlace(folder))
			places.append(Place(notebookId: nil, folderId: folder.id))
			for nb in store.notebooksIn(folder.id) {
				labels.append(notebookPlace(nb, folder))
				places.append(Place(notebookId: nb.id, folderId: nil))
			}
		}
		for nb in store.notebooksIn(nil) {
			labels.append(notebookPlace(nb))
			places.append(Place(notebookId: nb.id, folderId: nil))
		}
		return (labels, places)
	}

	static func placeOfNote(_ note: Note) -> Place {
		note.notebookId != nil ? Place(notebookId: note.notebookId, folderId: nil) : Place(notebookId: nil, folderId: note.folderId)
	}

	/// Text of the place of a note, or empty for a loose note.
	static func placeOf(_ store: NotesStore, _ note: Note) -> String {
		if let nb = store.getNotebook(note.notebookId) {
			return tr("notebook {name}", ["name": nb.name])
		}
		if let folder = store.getFolder(note.folderId) {
			return tr("folder {name}", ["name": folder.name])
		}
		return ""
	}

	static func formatDate(_ iso: String) -> String {
		guard let date = Model.parseIso(iso) else { return "" }
		let c = Calendar.current.dateComponents([.day, .month, .year], from: date)
		return tr("{month}/{day}/{year}", [
			"day": String(format: "%02d", c.day ?? 0),
			"month": String(format: "%02d", c.month ?? 0),
			"year": c.year ?? 0,
		])
	}

	static func formatTime(_ when: Date = Date()) -> String {
		let c = Calendar.current.dateComponents([.hour, .minute], from: when)
		return String(format: "%02d:%02d", c.hour ?? 0, c.minute ?? 0)
	}

	/// What the trees say for a note: title, status, place, tags and date.
	static func noteDescription(_ note: Note, place: String, withLane: Bool = false) -> String {
		var parts = [noteTitle(note)]
		if withLane {
			parts.append(laneName(note.laneId))
		}
		if !place.isEmpty {
			parts.append(place)
		}
		if !note.tags.isEmpty {
			parts.append(tr("tags {tags}", ["tags": note.tags.joined(separator: ", ")]))
		}
		let date = formatDate(note.updatedAt)
		if !date.isEmpty {
			parts.append(tr("updated on {date}", ["date": date]))
		}
		return parts.joined(separator: ", ")
	}

	static func laneNode(_ laneId: String, _ count: Int) -> String {
		tr("{lane}, {count}", ["lane": laneName(laneId), "count": notesCount(count)])
	}

	static func movedTo(_ laneId: String) -> String {
		tr("Status updated to {lane}", ["lane": laneName(laneId)])
	}

	static func movedToPlace(_ label: String) -> String {
		tr("Moved to {place}", ["place": label])
	}

	static func moreNotes(_ remaining: Int, _ page: Int) -> String {
		tr("Show {count} more notes ({remaining} not shown yet)", ["count": min(page, remaining), "remaining": remaining])
	}

	static func createLabels() -> [String] {
		[ui("&Note…"), ui("Note&book…"), ui("&Folder…")]
	}

	static func askNotebookName(_ folder: Folder?) -> String {
		if let folder {
			return tr("Name of the new notebook (in the folder {folder}):", ["folder": folder.name])
		}
		return tr("Name of the new notebook:")
	}

	static func notebookCreated(_ name: String) -> String {
		tr("Notebook {name} created", ["name": name])
	}

	static func folderCreated(_ name: String) -> String {
		tr("Folder {name} created", ["name": name])
	}

	static func alreadyFirst() -> String {
		tr("Already in the first lane")
	}

	static func alreadyLast() -> String {
		tr("Already in the last lane")
	}

	static func lanesSummary(_ counts: [String: Int]) -> String {
		Model.laneIds.map { "\(laneName($0)) \(counts[$0] ?? 0)" }.joined(separator: ", ")
	}

	static func storeError(_ error: Error, folder: String = "") -> String {
		let kind = (error as? StoreError)?.kind ?? .write
		switch kind {
		case .tooLarge:
			return tr("The file is larger than 200 MB and was not opened.")
		case .invalidImport:
			return tr("This file has no Notas Workflow NVDA notes.")
		case .notFound:
			return tr("This item no longer exists.")
		case .emptyName:
			return tr("The name cannot be empty.")
		default:
			return tr("Could not save the notes in {folder}. Check that the folder exists and can be written.", ["folder": folder])
		}
	}

	static func corruptWarning(_ savedAs: String, _ restored: Bool) -> String {
		if restored {
			return tr("The saved notes were damaged. The file was kept as {name} and the backup copy was used.", ["name": savedAs])
		}
		return tr("The saved notes were damaged. The file was kept as {name} and no backup copy could be used.", ["name": savedAs])
	}

	static func formatName(_ kind: String, applied: Bool) -> String {
		let names = [
			"bold": tr("Bold"),
			"italic": tr("Italic"),
			"strike": tr("Strikethrough"),
			"code": tr("Inline code"),
			"heading2": tr("Heading 2"),
			"heading3": tr("Heading 3"),
			"bullet": tr("Bulleted list"),
			"ordered": tr("Numbered list"),
			"quote": tr("Quote"),
			"divider": tr("Divider"),
		]
		let name = names[kind] ?? kind
		return applied ? name : tr("{format} removed", ["format": name])
	}
}
