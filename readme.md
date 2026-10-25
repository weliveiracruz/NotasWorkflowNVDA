# Notas Workflow NVDA

NVDA add-on to organize notes and tasks in status lanes (To do, In progress, Blocked, Done), grouped in notebooks and folders, with formatted content, automatic saving and search. Everything works from the keyboard, with spoken feedback, and stays fast with tens of thousands of notes.

## The main window

Press **NVDA+Alt+N** (or NVDA menu, Tools, **Notas Workflow NVDA…**). The window has:

* **Show**: all notes, loose notes (neither in a notebook nor in a folder), recent notes (the 10 changed last), one notebook or one folder.
* **Notes**: the notes in a tree with one branch per lane ("To do, 3 notes"). Lanes start closed: Right Arrow opens one, Left Arrow closes it. Enter opens the note, Delete deletes it (after confirming), **Alt+Shift+Right Arrow** and **Alt+Shift+Left Arrow** change its status, **Ctrl+Shift+Up Arrow** and **Ctrl+Shift+Down Arrow** move it up or down inside its lane. Each lane shows 200 notes at a time; "Show more notes" at the end shows the next ones.
* **Create…**: a menu to create a note, a notebook or a folder.
* **Update the task status…**: a menu with the other statuses.
* **Move to…**: moves the note to a notebook, directly to a folder, or makes it loose.
* **Location** (in New note, in the note window and in Move to) is a tree that opens like the lanes: each folder starts closed, with its notebooks inside; choosing the folder itself puts the note directly in it.
* **Delete**, **Search…**, **Notebooks and folders…** and **Close** (Esc).
* **Export…**: exports the selected note, a notebook or a folder as a document (see below).
* **User manual…** (Alt+N): opens the detailed user manual (in Brazilian Portuguese) in NVDA's browseable window, with headings, tables and a table of contents. A command without a default shortcut in Input gestures opens it too.

## Notes

**Create… > Note…** (or NVDA+Alt+F from anywhere) asks for the title, the location (loose, a folder or a notebook) and the status, and then opens the note window. The note window has the title, location, status and the content. If you change the status or the location there, closing the window puts the focus on the next note of the same lane, so a lane can be handled one note after the other. It saves by itself 2 seconds after you stop typing; Ctrl+S saves at once and closing the window (Esc or Save and close) always saves. Nothing is lost.

The content is plain text with a light markup:

| Type | To get |
|---|---|
| `## Title` or `### Title` | Heading 2 or 3 |
| `- item` | Bulleted list |
| `1. item` | Numbered list |
| `> text` | Quote |
| `---` | Divider |
| `**text**` | Bold (Ctrl+B) |
| `*text*` | Italic (Ctrl+I) |
| `~~text~~` | Strikethrough |
| `` `text` `` | Inline code |

The **Formatting…** button opens a menu with every format; it applies to the selected text or to the current line, and choosing it again removes it.

## Search

**NVDA+Alt+B** (or Search… in the window) searches the title and the content, ignoring accents and case, while you type. Results show the title, an excerpt, the relevance and the date; Enter opens the note. The search takes a fraction of a second even with 100,000 notes.

## Notebooks and folders

The **Notebooks and folders…** window shows each folder with its notebooks and its notes, a "Without folder" branch with the other notebooks and a "Loose notes" branch. Enter opens a note. **Create…** creates a note, notebook or folder in the selected place; **Rename…** (F2) renames a folder or notebook or changes the title of a note; **Move to…** moves a note or a notebook; **Delete** (Delete key) deletes. Deleting a notebook or a folder never deletes notes: they become loose.

## Export as a document

**Export…** (Alt+X) in the main window opens a menu with **Selected note…**, **Notebook…** and **Folder…**, then asks the format: **Word document (.docx)**, **Markdown (.md)** or **HTML page (.html)**. A notebook or a folder can go to **one file with all the notes** or to **one file for each note** (in a new folder named after the notebook or folder, with a subfolder for each notebook). Each note brings its title, status, tags, dates and formatted content; the titles are real headings, easy to navigate with a screen reader. Nothing is overwritten without asking, the files are written in the background, and NVDA says how many notes were exported and where.

## Shortcuts

| Shortcut | Action |
|---|---|
| NVDA+Alt+N | Open the Notas Workflow NVDA window |
| NVDA+Alt+F | New note |
| NVDA+Alt+B | Search the notes |
| Alt+Shift+Right and Left Arrow | Next or previous status of the note |
| Ctrl+Shift+Up and Down Arrow | Move the note up or down inside its lane |
| Ctrl+S, Ctrl+B, Ctrl+I | Save, bold and italic in the note window |

They can be changed in NVDA, Preferences, Input gestures, Notas Workflow NVDA category, where there is also a command, without shortcut, that says how many notes each lane has.

## Where the notes are

In the file `NotasWorkflowNVDA-data.json` of the notes folder, by default the `NotasWorkflowNVDA` folder inside the NVDA settings folder (`%APPDATA%\nvda`). NVDA, Preferences, Settings, **Notas Workflow NVDA** category changes the folder: choose a folder of OneDrive or Google Drive for computers to have the notes on every computer. There you also choose the automatic saving time and **Import notes…** and **Export notes…**.

Every change is saved in the background, in a safe way: the previous file is kept as `NotasWorkflowNVDA-data.json.bak`, and everything pending is written before NVDA exits. If the file is damaged, it is kept with another name and the backup copy is used. Uninstalling the add-on does not delete the notes.

## Many notes

The add-on was measured with 100,000 notes: NVDA starts at once (the notes are read in the background), and changing a status, opening a note, saving and searching take fractions of a second.

## Privacy

The add-on does not use the internet: no note leaves the computer, and the content of the notes never goes to the NVDA log.
