# Notas Workflow NVDA

NVDA add-on with the same workflow as the Notas Workflow web app: notes organized in status lanes (To do, In progress, Blocked, Done), grouped in notebooks and folders, with tags, formatted content, automatic saving and search. Everything works from the keyboard, with spoken feedback, without a browser.

## The main window

Press **NVDA+Alt+N** (or NVDA menu, Tools, **Notas Workflow NVDA…**). The window has:

* **Show**: all notes, loose notes (without notebook), recent notes (the 10 changed last), one notebook or one folder.
* **View**: **Lanes (tree)**, with one branch per lane ("To do, 3 notes"), or **Table**, with the columns Title, Status, Notebook, Tags and Updated on.
* **Notes**: the list itself. Enter opens the note, Delete deletes it (after confirming), **Alt+Shift+Right Arrow** moves it to the next lane and **Alt+Shift+Left Arrow** to the previous one.
* Buttons **New note…**, **Open**, **Move to…** (menu with the other lanes), **Change notebook…**, **Delete**, **Search…**, **Notebooks and folders…** and **Close** (Esc).

## Notes

**New note** (NVDA+Alt+F or the New note… button) asks for the title, the notebook and the status, and then opens the note window. The note window has the title, notebook, status, tags (separated by commas) and the content. It saves by itself 2 seconds after you stop typing; Ctrl+S saves at once and closing the window (Esc or Save and close) always saves. Nothing is lost.

The content is plain text with a light markup, the same formats of the web editor:

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

**NVDA+Alt+B** (or Search… in the window) searches the title, the content and the tags, ignoring accents and case, while you type. Results show the title, an excerpt, the relevance and the date; Enter opens the note.

## Notebooks and folders

The **Notebooks and folders…** window shows each folder with its notebooks and a "Without folder" branch. It creates notebooks (inside the selected folder) and folders, renames (F2), moves a notebook to another folder and deletes (Delete). Deleting a notebook or a folder never deletes notes: they become loose.

## Shortcuts

| Shortcut | Action |
|---|---|
| NVDA+Alt+N | Open the Notas Workflow NVDA window |
| NVDA+Alt+F | New note |
| NVDA+Alt+B | Search the notes |
| Alt+Shift+Right and Left Arrow | Move the note to the next or previous lane |
| Ctrl+S, Ctrl+B, Ctrl+I | Save, bold and italic in the note window |

They can be changed in NVDA, Preferences, Input gestures, Notas Workflow NVDA category, where there is also a command, without shortcut, that says how many notes each lane has.

## Where the notes are

In the file `NotasWorkflowNVDA-data.json` of the notes folder, by default the `NotasWorkflowNVDA` folder inside the NVDA settings folder (`%APPDATA%\nvda`). NVDA, Preferences, Settings, **Notas Workflow NVDA** category changes the folder: choose a folder of OneDrive or Google Drive for computers to have the notes on every computer. There you also choose the automatic saving time and **Import notes…** and **Export notes…**.

Every change is saved at once, in a safe way: the previous file is kept as `NotasWorkflowNVDA-data.json.bak`. If the file is damaged, it is kept with another name and the backup copy is used. Uninstalling the add-on does not delete the notes.

## Notes of the web app

Export and import use the format of the web app (the same fields of notes, notebooks and folders). To bring the notes of the browser, open the web app, press F12, go to Console and run `copy(JSON.stringify({notes: JSON.parse(localStorage["notas-workflow:notes"] || "[]"), notebooks: JSON.parse(localStorage["notas-workflow:notebooks"] || "[]")}))`. Paste the text in a file ending in `.json` and use **Import notes…**. Notes with the same identifier keep the version changed last.

## Privacy

The add-on does not use the internet: no note leaves the computer, and the content of the notes never goes to the NVDA log.
