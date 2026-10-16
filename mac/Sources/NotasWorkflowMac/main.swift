// Notas Workflow Mac - main.swift
// The app: menu bar, the item in the status bar (like the NVDA Tools menu item of the
// add-on), the global shortcuts, and saving everything before quitting.
// Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
// This file is covered by the GNU General Public License, version 2.

import AppKit
import Carbon.HIToolbox
import NotasCore

final class AppDelegate: NSObject, NSApplicationDelegate {
	var statusItem: NSStatusItem?
	let controller = AppController.shared

	func applicationDidFinishLaunching(_ notification: Notification) {
		NSApp.mainMenu = buildMainMenu()
		buildStatusItem()
		// Option+Shift+Command+N, F and B: NVDA+Alt+N, F and B of the add-on
		// (Control+Option is the VoiceOver key, so it is not used).
		HotKeys.register(keyCode: kVK_ANSI_N) { [controller] in controller.shortcutOpenWindow() }
		HotKeys.register(keyCode: kVK_ANSI_F) { [controller] in controller.shortcutNewNote() }
		HotKeys.register(keyCode: kVK_ANSI_B) { [controller] in controller.shortcutSearch() }
		HotKeys.register(keyCode: kVK_ANSI_L) { [controller] in controller.sayLanesSummary() }
		controller.start()
		controller.openWindow()
	}

	func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
		// The app keeps running for the global shortcuts, like the add-on inside NVDA.
		false
	}

	func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
		if !flag {
			controller.openWindow()
		}
		return true
	}

	func applicationWillTerminate(_ notification: Notification) {
		// Nothing is lost: the open note and the last changes are written before quitting.
		controller.terminate()
	}

	// MARK: menus

	private func item(_ title: String, _ action: Selector?, _ key: String = "", _ modifiers: NSEvent.ModifierFlags = [.command]) -> NSMenuItem {
		let item = NSMenuItem(title: title, action: action, keyEquivalent: key)
		item.keyEquivalentModifierMask = modifiers
		if let action, responds(to: action) {
			item.target = self
		}
		return item
	}

	private func buildMainMenu() -> NSMenu {
		let main = NSMenu()
		let name = Messages.appName

		let appMenu = NSMenu(title: name)
		appMenu.addItem(item(ui("About {name}", ["name": name]), #selector(NSApplication.orderFrontStandardAboutPanel(_:))))
		appMenu.addItem(.separator())
		appMenu.addItem(item(ui("Settings…"), #selector(openSettings), ","))
		appMenu.addItem(.separator())
		appMenu.addItem(item(ui("Hide {name}", ["name": name]), #selector(NSApplication.hide(_:)), "h"))
		appMenu.addItem(item(ui("Quit {name}", ["name": name]), #selector(NSApplication.terminate(_:)), "q"))
		addSubmenu(main, appMenu)

		// Without the Edit menu, Command+C, V, X, A and Z do not work in the text fields.
		let edit = NSMenu(title: ui("Edit"))
		edit.addItem(item(ui("Undo"), Selector(("undo:")), "z"))
		edit.addItem(item(ui("Redo"), Selector(("redo:")), "z", [.command, .shift]))
		edit.addItem(.separator())
		edit.addItem(item(ui("Cut"), #selector(NSText.cut(_:)), "x"))
		edit.addItem(item(ui("Copy"), #selector(NSText.copy(_:)), "c"))
		edit.addItem(item(ui("Paste"), #selector(NSText.paste(_:)), "v"))
		edit.addItem(item(ui("Select All"), #selector(NSText.selectAll(_:)), "a"))
		addSubmenu(main, edit)

		let notes = NSMenu(title: ui("Notes"))
		notes.addItem(item(ui("&Notas Workflow NVDA…"), #selector(openMainWindow), "0"))
		notes.addItem(item(ui("New note"), #selector(newNote)))
		notes.addItem(item(ui("Search notes"), #selector(search)))
		notes.addItem(item(ui("Say how many notes each lane has"), #selector(lanesSummary)))
		addSubmenu(main, notes)

		let window = NSMenu(title: ui("Window"))
		window.addItem(item(ui("Minimize"), #selector(NSWindow.performMiniaturize(_:)), "m"))
		addSubmenu(main, window)
		NSApp.windowsMenu = window
		return main
	}

	private func addSubmenu(_ main: NSMenu, _ menu: NSMenu) {
		let holder = NSMenuItem(title: menu.title, action: nil, keyEquivalent: "")
		holder.submenu = menu
		main.addItem(holder)
	}

	private func buildStatusItem() {
		let status = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
		status.button?.title = "NW"
		status.button?.setAccessibilityLabel(Messages.appName)
		if let image = NSImage(systemSymbolName: "checklist", accessibilityDescription: Messages.appName) {
			status.button?.image = image
			status.button?.title = ""
		}
		let menu = NSMenu()
		menu.addItem(item(ui("&Notas Workflow NVDA…"), #selector(openMainWindow)))
		menu.addItem(item(ui("New note"), #selector(newNote)))
		menu.addItem(item(ui("Search notes"), #selector(search)))
		menu.addItem(item(ui("Say how many notes each lane has"), #selector(lanesSummary)))
		menu.addItem(.separator())
		menu.addItem(item(ui("Settings…"), #selector(openSettings)))
		menu.addItem(item(ui("Quit {name}", ["name": Messages.appName]), #selector(NSApplication.terminate(_:))))
		status.menu = menu
		statusItem = status
	}

	@objc func openMainWindow() {
		controller.shortcutOpenWindow()
	}

	@objc func newNote() {
		controller.shortcutNewNote()
	}

	@objc func search() {
		controller.shortcutSearch()
	}

	@objc func lanesSummary() {
		controller.sayLanesSummary()
	}

	@objc func openSettings() {
		NSApp.activate(ignoringOtherApps: true)
		controller.openSettings()
	}
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
