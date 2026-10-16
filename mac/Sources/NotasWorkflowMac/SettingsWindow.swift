// Notas Workflow Mac - SettingsWindow.swift
// Settings (Command+Comma): where the notes are stored, automatic saving, import and
// export, and opening at login (port of settingsPanel.py).
// Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
// This file is covered by the GNU General Public License, version 2.

import AppKit
import NotasCore
import ServiceManagement
import UniformTypeIdentifiers

final class SettingsWindowController {
	unowned let controller: AppController
	let window = KeyWindow(title: ui("Settings"), resizable: false)
	let folderEdit = TextField(label: accessibleName(ui("Notes &folder:")), width: 360)
	let autoSaveChoice = ChoiceBox(items: (1...30).map { String($0) }, label: accessibleName(ui("&Save automatically after (seconds):")))
	let announceCheck = NSButton(checkboxWithTitle: ui("&Announce the automatic saving"), target: nil, action: nil)
	let loginCheck = NSButton(checkboxWithTitle: ui("Open at &login"), target: nil, action: nil)
	var importButton: ActionButton!
	var exportButton: ActionButton!

	init(controller: AppController) {
		self.controller = controller
		folderEdit.stringValue = Settings.dataFolder.isEmpty ? Settings.defaultDataFolder() : Settings.dataFolder
		autoSaveChoice.selectItem(at: Settings.autoSaveSeconds - 1)
		announceCheck.state = Settings.announceAutoSave ? .on : .off
		loginCheck.state = SMAppService.mainApp.status == .enabled ? .on : .off
		let browseButton = ActionButton(ui("B&rowse…")) { [unowned self] in self.onBrowse() }
		let defaultButton = ActionButton(ui("Use the &default folder")) { [unowned self] in self.onDefault() }
		importButton = ActionButton(ui("&Import notes…")) { [unowned self] in self.onImport() }
		exportButton = ActionButton(ui("&Export notes…")) { [unowned self] in self.onExport() }
		let okButton = ActionButton("OK", key: "\r", modifiers: []) { [unowned self] in self.onOK() }
		let cancelButton = ActionButton(ui("Cancel")) { [unowned self] in endModalWindow(self.window) }
		layoutWindow(window, [
			labelledRow(ui("Notes &folder:"), folderEdit),
			buttonRow([browseButton, defaultButton]),
			labelledRow(ui("&Save automatically after (seconds):"), autoSaveChoice),
			announceCheck,
			loginCheck,
			buttonRow([importButton, exportButton]),
			buttonRow([cancelButton, okButton]),
		])
	}

	func run() {
		window.makeFirstResponder(folderEdit)
		runModalWindow(window)
	}

	func onBrowse() {
		let panel = NSOpenPanel()
		panel.title = ui("Folder of the notes")
		panel.canChooseDirectories = true
		panel.canChooseFiles = false
		panel.canCreateDirectories = true
		panel.allowsMultipleSelection = false
		let current = folderEdit.stringValue
		if !current.isEmpty {
			panel.directoryURL = URL(fileURLWithPath: current)
		}
		if panel.runModal() == .OK, let url = panel.url {
			folderEdit.stringValue = url.path
		}
		window.makeFirstResponder(folderEdit)
	}

	func onDefault() {
		folderEdit.stringValue = Settings.defaultDataFolder()
		window.makeFirstResponder(folderEdit)
	}

	func onImport() {
		let panel = NSOpenPanel()
		panel.title = ui("Import notes")
		panel.canChooseFiles = true
		panel.canChooseDirectories = false
		panel.allowsMultipleSelection = false
		panel.allowedContentTypes = [.json]
		if panel.runModal() == .OK, let url = panel.url {
			controller.importNotes(url.path)
		}
		window.makeFirstResponder(importButton)
	}

	func onExport() {
		let panel = NSSavePanel()
		panel.title = ui("Export notes")
		panel.nameFieldStringValue = "notas-workflow-nvda.json"
		panel.allowedContentTypes = [.json]
		if panel.runModal() == .OK, let url = panel.url {
			controller.exportNotes(url.path)
		}
		window.makeFirstResponder(exportButton)
	}

	/// The folder typed, or "" when it is the default one.
	func chosenFolder() -> String {
		let path = (folderEdit.stringValue.trimmingCharacters(in: .whitespaces) as NSString).expandingTildeInPath
		if path.isEmpty || URL(fileURLWithPath: path).standardizedFileURL.path == URL(fileURLWithPath: Settings.defaultDataFolder()).standardizedFileURL.path {
			return ""
		}
		return path
	}

	func isValid() -> Bool {
		let path = chosenFolder()
		var isDir: ObjCBool = false
		if !path.isEmpty && !(path.hasPrefix("/") && FileManager.default.fileExists(atPath: path, isDirectory: &isDir) && isDir.boolValue && FileManager.default.isWritableFile(atPath: path)) {
			Prompts.message(tr("The notes folder must be an existing folder that can be written. Choose it with Browse."))
			window.makeFirstResponder(folderEdit)
			return false
		}
		return true
	}

	func onOK() {
		guard isValid() else { return }
		let folder = chosenFolder()
		let changed = folder != Settings.dataFolder
		Settings.dataFolder = folder
		Settings.autoSaveSeconds = autoSaveChoice.indexOfSelectedItem + 1
		Settings.announceAutoSave = announceCheck.state == .on
		let wantsLogin = loginCheck.state == .on
		if wantsLogin != (SMAppService.mainApp.status == .enabled) {
			do {
				if wantsLogin {
					try SMAppService.mainApp.register()
				} else {
					try SMAppService.mainApp.unregister()
				}
			} catch {
				controller.speak(tr("Could not change the opening at login."))
			}
		}
		endModalWindow(window)
		if changed {
			controller.changeDataFolder()
		}
	}
}
