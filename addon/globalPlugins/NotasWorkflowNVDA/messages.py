# -*- coding: UTF-8 -*-
# NotasWorkflowNVDA - messages.py
# Translated texts shared by the windows and the commands.
# Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
# This file is covered by the GNU General Public License, version 2.

import datetime

import addonHandler

from . import model

addonHandler.initTranslation()


def laneName(laneId):
	names = {
		# Translators: name of the first lane (status) of the notes.
		"todo": _("To do"),
		# Translators: name of the second lane (status) of the notes.
		"inprogress": _("In progress"),
		# Translators: name of the third lane (status) of the notes.
		"blocked": _("Blocked"),
		# Translators: name of the fourth lane (status) of the notes.
		"done": _("Done"),
	}
	return names.get(laneId, names["todo"])


def laneNames():
	return [laneName(lane) for lane in model.LANE_IDS]


def untitled():
	# Translators: shown instead of the title of a note without title.
	return _("Untitled")


def noteTitle(note):
	return note.get("title") or untitled()


def notesCount(count):
	if count == 1:
		# Translators: number of notes, singular.
		return _("1 note")
	# Translators: number of notes, plural.
	return _("{count} notes").format(count=count)


def notebooksCount(count):
	if count == 1:
		# Translators: number of notebooks, singular.
		return _("1 notebook")
	# Translators: number of notebooks, plural.
	return _("{count} notebooks").format(count=count)


def looseNote():
	# Translators: place of a note that is neither in a notebook nor in a folder.
	return _("Loose note (no notebook or folder)")


def notebookPlace(notebook, folder=None):
	if folder:
		# Translators: a notebook inside a folder, in the Location box and the Move to list.
		return _("Notebook {name} (folder {folder})").format(name=notebook["name"], folder=folder["name"])
	# Translators: a notebook that is not in a folder, in the Location box and the Move to list.
	return _("Notebook {name}").format(name=notebook["name"])


def folderPlace(folder):
	# Translators: a folder (the note goes directly into it), in the Location box and the Move to list.
	return _("Folder {name}").format(name=folder["name"])


def folderLocation(folder, notebooks):
	# Translators: a folder in the Location tree (the note goes directly into it, or into one of its notebooks, shown inside); {count} is its number of notebooks.
	return _("Folder {name}, {count}").format(name=folder["name"], count=notebooksCount(notebooks))


def locationChoices(store):
	"""(labels, [(notebookId, folderId)]) of every place a note can be: loose, each
	folder followed by its notebooks, then the notebooks without folder."""
	labels = [looseNote()]
	places = [(None, None)]
	for folder in store.folders:
		labels.append(folderPlace(folder))
		places.append((None, folder["id"]))
		for nb in store.notebooksIn(folder["id"]):
			labels.append(notebookPlace(nb, folder))
			places.append((nb["id"], None))
	for nb in store.notebooksIn(None):
		labels.append(notebookPlace(nb))
		places.append((nb["id"], None))
	return labels, places


def placeOf(store, note):
	"""Text of the place of a note, or empty for a loose note."""
	if note.get("notebookId"):
		nb = store.getNotebook(note["notebookId"])
		if nb:
			# Translators: part of the description of a note: its notebook.
			return _("notebook {name}").format(name=nb["name"])
	if note.get("folderId"):
		folder = store.getFolder(note["folderId"])
		if folder:
			# Translators: part of the description of a note: the folder it is directly in.
			return _("folder {name}").format(name=folder["name"])
	return ""


def formatDate(iso):
	dt = model.parseIso(iso)
	if dt is None:
		return ""
	local = dt.astimezone()
	# Translators: date format; keep {day}, {month} and {year}, change only the order and separators.
	return _("{month}/{day}/{year}").format(day="%02d" % local.day, month="%02d" % local.month, year=local.year)


def formatTime(when=None):
	when = when or datetime.datetime.now()
	return "%02d:%02d" % (when.hour, when.minute)


def noteDescription(note, place, withLane=False):
	"""What the trees say for a note: title, status, place and date."""
	parts = [noteTitle(note)]
	if withLane:
		parts.append(laneName(note["laneId"]))
	if place:
		parts.append(place)
	date = formatDate(note.get("updatedAt"))
	if date:
		# Translators: part of the description of a note: last change.
		parts.append(_("updated on {date}").format(date=date))
	return ", ".join(parts)


def laneNode(laneId, count):
	# Translators: a lane in the tree, for example "To do, 3 notes".
	return _("{lane}, {count}").format(lane=laneName(laneId), count=notesCount(count))


def movedTo(laneId):
	# Translators: spoken after the status (lane) of a note changes.
	return _("Status updated to {lane}").format(lane=laneName(laneId))


def movedToPlace(label):
	# Translators: spoken after a note or notebook is moved; {place} is a folder, a notebook or "Loose note".
	return _("Moved to {place}").format(place=label)


def moreNotes(remaining, page):
	# Translators: last item of a long list in a tree: Enter shows the next notes.
	return _("Show {count} more notes ({remaining} not shown yet)").format(count=min(page, remaining), remaining=remaining)


def createLabels():
	return [
		# Translators: item of the Create menu.
		_("&Note…"),
		# Translators: item of the Create menu.
		_("Note&book…"),
		# Translators: item of the Create menu.
		_("&Folder…"),
		# Translators: item of the Create menu: a note with the text of a Word, PowerPoint, text, HTML or e-mail document.
		_("Note from &document…"),
	]


def documentWildcard():
	"""Types of file of the dialog that chooses a document to read."""
	parts = [
		# Translators: type of file in the dialog that chooses a document to read into a note.
		_("Documents (*.docx, *.pptx, *.txt, *.html, *.eml)") + "|*.docx;*.pptx;*.txt;*.html;*.htm;*.eml",
		# Translators: type of file in the dialog that chooses a document to read into a note.
		_("Word document (*.docx)") + "|*.docx",
		# Translators: type of file in the dialog that chooses a document to read into a note.
		_("PowerPoint presentation (*.pptx)") + "|*.pptx",
		# Translators: type of file in the dialog that chooses a document to read into a note.
		_("Text (*.txt)") + "|*.txt",
		# Translators: type of file in the dialog that chooses a document to read into a note.
		_("HTML page (*.html, *.htm)") + "|*.html;*.htm",
		# Translators: type of file in the dialog that chooses a document to read into a note.
		_("E-mail message (*.eml)") + "|*.eml",
	]
	return "|".join(parts)


def documentLabels():
	"""Words written in the text of a presentation or an e-mail read into a note."""
	return {
		# Translators: heading of a slide of a presentation read into a note.
		"slide": _("Slide {number}"),
		# Translators: heading of a slide of a presentation read into a note, with the title of the slide.
		"slideTitled": _("Slide {number}: {title}"),
		# Translators: line before the speaker notes of a slide read into a note.
		"notes": _("Speaker notes:"),
		# Translators: line of an e-mail read into a note: who sent it.
		"from": _("From:"),
		# Translators: line of an e-mail read into a note: to whom it was sent.
		"to": _("To:"),
		# Translators: line of an e-mail read into a note: copy.
		"cc": _("Cc:"),
		# Translators: line of an e-mail read into a note: when it was sent.
		"date": _("Date:"),
		# Translators: line of an e-mail read into a note: the names of the attached files.
		"attachments": _("Attachments:"),
	}


def documentDate(when):
	"""Date and time of an e-mail read into a note."""
	return "%s %s" % (formatDate(model.nowIso(when)), formatTime(when.astimezone()))


def documentError(kind, name):
	if kind == "unsupported":
		# Translators: spoken when the chosen file cannot be read; {file} is its name.
		return _("{file} cannot be read. Choose a Word (.docx), PowerPoint (.pptx), text (.txt), HTML or e-mail (.eml) document.").format(file=name)
	if kind == "tooBig":
		# Translators: spoken when the chosen document is too big; {file} is its name.
		return _("{file} has more than 50 MB and was not read.").format(file=name)
	if kind == "damaged":
		# Translators: spoken when the chosen document is damaged or protected; {file} is its name.
		return _("Could not read {file}: the file is damaged or protected by a password.").format(file=name)
	if kind == "empty":
		# Translators: spoken when the chosen document has no text; {file} is its name.
		return _("{file} has no text.").format(file=name)
	# Translators: spoken when the chosen document could not be opened; {file} is its name.
	return _("Could not open {file}.").format(file=name)


def readingDocument():
	# Translators: spoken while a document is read to create a note or to insert it in a note.
	return _("Reading the document…")


def documentNoRoom():
	# Translators: spoken by Insert document when the note already has the most text a note can hold.
	return _("The note is full (up to 1 MB): nothing was inserted.")


def documentCut():
	# Translators: spoken when the text of a document did not fit in the note.
	return _("The text was too long: only its first part was used (a note holds up to 1 MB).")


def exportLabels(withNote):
	"""Items of the Export menu: the selected note only when there is one."""
	labels = [
		# Translators: item of the Export menu: exports a notebook.
		_("Note&book…"),
		# Translators: item of the Export menu: exports a folder.
		_("&Folder…"),
	]
	if withNote:
		# Translators: item of the Export menu: exports the note selected in the list.
		labels.insert(0, _("Selected &note…"))
	return labels


def exportFormats():
	"""Names of the export formats, in the order of exporter.FORMATS."""
	return [
		# Translators: export format.
		_("Word document (.docx)"),
		# Translators: export format.
		_("Markdown (.md)"),
		# Translators: export format.
		_("HTML page (.html)"),
	]


def exportWildcard(fmt):
	wildcards = {
		# Translators: type of file in the dialog that chooses where to export.
		"docx": _("Word document (*.docx)|*.docx"),
		# Translators: type of file in the dialog that chooses where to export.
		"md": _("Markdown (*.md)|*.md"),
		# Translators: type of file in the dialog that chooses where to export.
		"html": _("HTML page (*.html)|*.html"),
	}
	return wildcards[fmt]


def exportModes():
	return [
		# Translators: how a notebook or folder is exported.
		_("One file with all the notes"),
		# Translators: how a notebook or folder is exported.
		_("One file for each note"),
	]


def noteDetails(note, place=""):
	"""Lines written under the title of an exported note: status, place and dates."""
	# Translators: line of an exported note: its status (lane).
	lines = [_("Status: {lane}").format(lane=laneName(note["laneId"]))]
	if place:
		# Translators: line of an exported note: its notebook or folder.
		lines.append(_("Location: {place}").format(place=place))
	created = formatDate(note.get("createdAt"))
	updated = formatDate(note.get("updatedAt"))
	if created and updated:
		# Translators: line of an exported note: when it was created and changed last.
		lines.append(_("Created on {created}, updated on {updated}").format(created=created, updated=updated))
	return lines


def exportIntro(count):
	# Translators: paragraph at the start of an exported notebook or folder; {count} is "3 notes".
	return _("Exported from Notas Workflow NVDA on {date}: {count}.").format(date=formatDate(model.nowIso()), count=notesCount(count))


def directInFolder():
	# Translators: heading, in an exported folder, of the notes put directly in it (not in a notebook).
	return _("Notes directly in the folder")


def nothingToExport(name):
	# Translators: spoken when the notebook or folder chosen to export has no notes.
	return _("Nothing to export: {name} has no notes.").format(name=name)


def exported(count, path):
	# Translators: spoken after exporting to one file; {count} is "3 notes", {file} the name of the file.
	return _("Exported: {count}, in {file}").format(count=notesCount(count), file=path)


def exportedSeparate(count, folder):
	# Translators: spoken after exporting one file for each note; {count} is "3 notes", {folder} the folder created.
	return _("Exported: {count}, one file for each note, in the folder {folder}").format(count=notesCount(count), folder=folder)


def exportFailed(path):
	# Translators: error when the exported file cannot be written; {path} is the file or folder.
	return _("Could not export to {path}. Check that the folder exists and can be written.").format(path=path)




def notebookCreated(name):
	# Translators: spoken after a notebook is created.
	return _("Notebook {name} created").format(name=name)


def folderCreated(name):
	# Translators: spoken after a folder is created.
	return _("Folder {name} created").format(name=name)


def alreadyFirst():
	# Translators: spoken when the note is already in the first lane.
	return _("Already in the first lane")


def alreadyLast():
	# Translators: spoken when the note is already in the last lane.
	return _("Already in the last lane")


def alreadyTop():
	# Translators: spoken by Ctrl+Shift+Up Arrow when the note is already the first one of its lane.
	return _("Already at the top of the lane")


def alreadyBottom():
	# Translators: spoken by Ctrl+Shift+Down Arrow when the note is already the last one of its lane.
	return _("Already at the bottom of the lane")


def positionInLane(position, total):
	# Translators: spoken after Ctrl+Shift+Up or Down Arrow moves a note in its lane, for example "Position 2 of 5".
	return _("Position {position} of {total}").format(position=position, total=total)


def noOrderInRecent():
	# Translators: spoken by Ctrl+Shift+Up or Down Arrow in Recent notes (always ordered by the last change).
	return _("Recent notes are ordered by the last change; the order cannot be changed here")


def lanesSummary(counts):
	return ", ".join("%s %d" % (laneName(lane), counts.get(lane, 0)) for lane in model.LANE_IDS)


def storeError(error, folder=""):
	kind = getattr(error, "kind", "write")
	if kind == "tooLarge":
		# Translators: error when a file is too big.
		return _("The file is larger than 200 MB and was not opened.")
	if kind == "invalidImport":
		# Translators: error when the chosen file is not an export of Notas Workflow NVDA.
		return _("This file has no Notas Workflow NVDA notes.")
	if kind == "notFound":
		# Translators: error when the note (or notebook, folder) no longer exists.
		return _("This item no longer exists.")
	if kind == "emptyName":
		# Translators: error when a name was left empty.
		return _("The name cannot be empty.")
	# Translators: error when the notes cannot be saved; {folder} is the data folder.
	return _("Could not save the notes in {folder}. Check that the folder exists and can be written.").format(folder=folder)


def corruptWarning(savedAs, restored):
	if restored:
		# Translators: warning when the data file was damaged; {name} is the copy kept.
		return _("The saved notes were damaged. The file was kept as {name} and the backup copy was used.").format(name=savedAs)
	# Translators: warning when the data file was damaged and there was no backup.
	return _("The saved notes were damaged. The file was kept as {name} and no backup copy could be used.").format(name=savedAs)


def formatName(kind, applied):
	names = {
		# Translators: format of the note content.
		"bold": _("Bold"),
		# Translators: format of the note content.
		"italic": _("Italic"),
		# Translators: format of the note content.
		"strike": _("Strikethrough"),
		# Translators: format of the note content.
		"code": _("Inline code"),
		# Translators: format of the note content.
		"heading2": _("Heading 2"),
		# Translators: format of the note content.
		"heading3": _("Heading 3"),
		# Translators: format of the note content.
		"bullet": _("Bulleted list"),
		# Translators: format of the note content.
		"ordered": _("Numbered list"),
		# Translators: format of the note content.
		"quote": _("Quote"),
		# Translators: format of the note content.
		"divider": _("Divider"),
	}
	name = names[kind]
	if applied:
		return name
	# Translators: spoken when a format is removed from the text, for example "Bold removed".
	return _("{format} removed").format(format=name)
