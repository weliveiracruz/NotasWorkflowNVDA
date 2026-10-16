// Notas Workflow Mac - UI.swift
// Small pieces shared by the windows: a window that catches keys before its controls
// (like EVT_CHAR_HOOK in the add-on), buttons and fields with closures, labelled rows
// that VoiceOver reads with their labels, modal windows and VoiceOver announcements.
// Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
// This file is covered by the GNU General Public License, version 2.

import AppKit
import NotasCore

enum KeyCode {
	static let returnKey: UInt16 = 36
	static let enter: UInt16 = 76
	static let escape: UInt16 = 53
	static let backspace: UInt16 = 51
	static let forwardDelete: UInt16 = 117
	static let left: UInt16 = 123
	static let right: UInt16 = 124
	static let f2: UInt16 = 120
}

extension NSEvent {
	/// The modifiers that matter for shortcuts (no Caps Lock, Fn or numeric pad flags).
	var shortcutModifiers: NSEvent.ModifierFlags {
		modifierFlags.intersection([.command, .option, .control, .shift])
	}

	var isReturn: Bool {
		keyCode == KeyCode.returnKey || keyCode == KeyCode.enter
	}

	var isDelete: Bool {
		keyCode == KeyCode.backspace || keyCode == KeyCode.forwardDelete
	}

	var lowerChars: String {
		(charactersIgnoringModifiers ?? "").lowercased()
	}
}

/// A window whose keyHandler sees the keys before the focused control. Closing it (Esc,
/// the close button, Command+W) calls closeHandler.
final class KeyWindow: NSWindow, NSWindowDelegate {
	var keyHandler: ((NSEvent) -> Bool)?
	var closeHandler: (() -> Void)?

	convenience init(title: String, resizable: Bool = true) {
		var style: NSWindow.StyleMask = [.titled, .closable, .miniaturizable]
		if resizable {
			style.insert(.resizable)
		}
		self.init(contentRect: NSRect(x: 0, y: 0, width: 600, height: 400), styleMask: style, backing: .buffered, defer: false)
		self.title = title
		isReleasedWhenClosed = false
		delegate = self
		autorecalculatesKeyViewLoop = true
	}

	override func sendEvent(_ event: NSEvent) {
		if event.type == .keyDown {
			if event.keyCode == KeyCode.escape && event.shortcutModifiers.isEmpty, attachedSheet == nil {
				requestClose()
				return
			}
			if let handler = keyHandler, handler(event) {
				return
			}
		}
		super.sendEvent(event)
	}

	override func performKeyEquivalent(with event: NSEvent) -> Bool {
		if isKeyWindow, event.type == .keyDown {
			if event.shortcutModifiers == .command && event.lowerChars == "w" {
				requestClose()
				return true
			}
			if let handler = keyHandler, handler(event) {
				return true
			}
		}
		return super.performKeyEquivalent(with: event)
	}

	func requestClose() {
		if let closeHandler {
			closeHandler()
		} else {
			endModalWindow(self)
		}
	}

	func windowShouldClose(_ sender: NSWindow) -> Bool {
		requestClose()
		return false
	}
}

/// Shows a window as a modal dialog and returns when it is closed with endModalWindow.
func runModalWindow(_ window: NSWindow) {
	window.center()
	NSApp.activate(ignoringOtherApps: true)
	window.makeKeyAndOrderFront(nil)
	NSApp.runModal(for: window)
	window.orderOut(nil)
}

func endModalWindow(_ window: NSWindow) {
	if NSApp.modalWindow === window {
		NSApp.stopModal()
		// stopModal waits for an event to leave the modal loop: one is sent at once.
		if let event = NSEvent.otherEvent(with: .applicationDefined, location: .zero, modifierFlags: [], timestamp: 0, windowNumber: 0, context: nil, subtype: 0, data1: 0, data2: 0) {
			NSApp.postEvent(event, atStart: true)
		}
	}
	window.orderOut(nil)
}

/// A button that runs a closure. keyEquivalent: a Command shortcut of the window.
final class ActionButton: NSButton {
	var onPress: (() -> Void)?

	convenience init(_ title: String, key: String = "", modifiers: NSEvent.ModifierFlags = [.command], onPress: (() -> Void)? = nil) {
		self.init(frame: .zero)
		self.title = title
		bezelStyle = .rounded
		setButtonType(.momentaryPushIn)
		keyEquivalent = key
		keyEquivalentModifierMask = key.isEmpty ? [] : modifiers
		self.onPress = onPress
		target = self
		action = #selector(fire)
	}

	@objc func fire() {
		onPress?()
	}
}

final class ChoiceBox: NSPopUpButton {
	var onChange: (() -> Void)?

	convenience init(items: [String], label: String) {
		self.init(frame: .zero, pullsDown: false)
		setItems(items)
		setAccessibilityLabel(label)
		target = self
		action = #selector(changed)
	}

	func setItems(_ items: [String]) {
		removeAllItems()
		// addItems(withTitles:) drops repeated titles: items are added one by one.
		for item in items {
			menu?.addItem(NSMenuItem(title: item, action: nil, keyEquivalent: ""))
		}
	}

	var titles: [String] {
		itemArray.map(\.title)
	}

	@objc func changed() {
		onChange?()
	}
}

/// A single-line text field. onChange: every change; onEnter: Return.
final class TextField: NSTextField, NSTextFieldDelegate {
	var onChange: (() -> Void)?
	var onEnter: (() -> Bool)?
	var maxLength = Int.max

	convenience init(label: String, width: CGFloat = 380) {
		self.init(frame: .zero)
		isEditable = true
		isSelectable = true
		isBezeled = true
		bezelStyle = .squareBezel
		lineBreakMode = .byClipping
		usesSingleLineMode = true
		cell?.isScrollable = true
		setAccessibilityLabel(label)
		delegate = self
		translatesAutoresizingMaskIntoConstraints = false
		widthAnchor.constraint(greaterThanOrEqualToConstant: width).isActive = true
	}

	func controlTextDidChange(_ obj: Notification) {
		if stringValue.count > maxLength {
			stringValue = String(stringValue.prefix(maxLength))
		}
		onChange?()
	}

	func control(_ control: NSControl, textView: NSTextView, doCommandBy commandSelector: Selector) -> Bool {
		if commandSelector == #selector(NSResponder.insertNewline(_:)), let onEnter {
			return onEnter()
		}
		return false
	}
}

/// A multi-line text box in a scroll view.
final class TextArea: NSScrollView, NSTextViewDelegate {
	let textView: NSTextView
	var onChange: (() -> Void)?

	init(label: String, width: CGFloat, height: CGFloat, editable: Bool = true) {
		let size = NSSize(width: width, height: height)
		textView = NSTextView(frame: NSRect(origin: .zero, size: size))
		super.init(frame: NSRect(origin: .zero, size: size))
		textView.isRichText = false
		textView.importsGraphics = false
		textView.allowsUndo = true
		textView.isEditable = editable
		textView.isSelectable = true
		textView.isAutomaticQuoteSubstitutionEnabled = false
		textView.isAutomaticDashSubstitutionEnabled = false
		textView.isAutomaticTextReplacementEnabled = false
		textView.isAutomaticSpellingCorrectionEnabled = false
		textView.font = NSFont.systemFont(ofSize: NSFont.systemFontSize)
		textView.isVerticallyResizable = true
		textView.isHorizontallyResizable = false
		textView.autoresizingMask = [.width]
		textView.textContainer?.widthTracksTextView = true
		textView.minSize = NSSize(width: 0, height: height)
		textView.maxSize = NSSize(width: CGFloat.greatestFiniteMagnitude, height: CGFloat.greatestFiniteMagnitude)
		textView.setAccessibilityLabel(label)
		textView.delegate = self
		documentView = textView
		hasVerticalScroller = true
		borderType = .bezelBorder
		translatesAutoresizingMaskIntoConstraints = false
		widthAnchor.constraint(greaterThanOrEqualToConstant: width).isActive = true
		heightAnchor.constraint(greaterThanOrEqualToConstant: height).isActive = true
	}

	required init?(coder: NSCoder) {
		fatalError("not used")
	}

	var string: String {
		get { textView.string }
		set { textView.string = newValue }
	}

	func textDidChange(_ notification: Notification) {
		onChange?()
	}
}

func makeLabel(_ text: String) -> NSTextField {
	let label = NSTextField(labelWithString: text)
	label.setAccessibilityElement(false)
	return label
}

/// "Title: [field]" in one line. The control gets the label as its accessible name.
func labelledRow(_ labelText: String, _ control: NSView) -> NSStackView {
	let label = makeLabel(labelText)
	control.setAccessibilityLabel(accessibleName(labelText))
	let row = NSStackView(views: [label, control])
	row.orientation = .horizontal
	row.alignment = .firstBaseline
	row.spacing = 8
	return row
}

/// "Label:" above a big control.
func labelledBlock(_ labelText: String, _ control: NSView) -> NSStackView {
	let label = makeLabel(labelText)
	control.setAccessibilityLabel(accessibleName(labelText))
	let block = NSStackView(views: [label, control])
	block.orientation = .vertical
	block.alignment = .leading
	block.spacing = 4
	return block
}

/// The label as VoiceOver says it: without the final colon.
func accessibleName(_ label: String) -> String {
	var name = label.trimmingCharacters(in: .whitespaces)
	if name.hasSuffix(":") {
		name.removeLast()
	}
	return name
}

func buttonRow(_ buttons: [NSView]) -> NSStackView {
	let row = NSStackView(views: buttons)
	row.orientation = .horizontal
	row.spacing = 8
	return row
}

/// Puts the views one below the other in the window, with the usual margins.
func layoutWindow(_ window: NSWindow, _ views: [NSView]) {
	let stack = NSStackView(views: views)
	stack.orientation = .vertical
	stack.alignment = .leading
	stack.spacing = 10
	stack.edgeInsets = NSEdgeInsets(top: 16, left: 16, bottom: 16, right: 16)
	stack.translatesAutoresizingMaskIntoConstraints = false
	let content = NSView()
	content.addSubview(stack)
	NSLayoutConstraint.activate([
		stack.leadingAnchor.constraint(equalTo: content.leadingAnchor),
		stack.trailingAnchor.constraint(equalTo: content.trailingAnchor),
		stack.topAnchor.constraint(equalTo: content.topAnchor),
		stack.bottomAnchor.constraint(equalTo: content.bottomAnchor),
	])
	for view in views where view is NSScrollView {
		view.trailingAnchor.constraint(equalTo: stack.trailingAnchor, constant: -16).isActive = true
	}
	window.contentView = content
	window.setContentSize(content.fittingSize)
}

// MARK: - VoiceOver

enum Speech {
	/// Says the text with VoiceOver (what ui.message does in NVDA). A short delay lets
	/// VoiceOver first say the focus change that usually comes with the action.
	static func say(_ text: String) {
		guard !text.isEmpty else { return }
		DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
			let element: Any
			if let window = NSApp.keyWindow ?? NSApp.mainWindow {
				element = window
			} else {
				element = NSApp as Any
			}
			NSAccessibility.post(
				element: element,
				notification: .announcementRequested,
				userInfo: [
					.announcement: text,
					.priority: NSAccessibilityPriorityLevel.high.rawValue,
				]
			)
		}
	}
}

// MARK: - Prompts

enum Prompts {
	/// Shows a pop-up menu under the view and returns the chosen index, or nil.
	static func chooseFromMenu(_ view: NSView, _ labels: [String]) -> Int? {
		let menu = NSMenu()
		menu.autoenablesItems = false
		let picker = MenuPicker()
		for (index, label) in labels.enumerated() {
			let item = NSMenuItem(title: label, action: #selector(MenuPicker.pick(_:)), keyEquivalent: "")
			item.target = picker
			item.tag = index
			menu.addItem(item)
		}
		_ = menu.popUp(positioning: menu.items.first, at: NSPoint(x: 0, y: view.bounds.height + 4), in: view)
		return picker.chosen
	}

	/// Index chosen in a list, or nil.
	static func chooseItem(_ message: String, _ title: String, _ labels: [String], current: Int = 0) -> Int? {
		let alert = NSAlert()
		alert.messageText = title
		alert.informativeText = message
		let box = ChoiceBox(items: labels, label: accessibleName(message))
		box.frame = NSRect(x: 0, y: 0, width: 360, height: 26)
		if !labels.isEmpty {
			box.selectItem(at: max(0, min(current, labels.count - 1)))
		}
		alert.accessoryView = box
		alert.addButton(withTitle: "OK")
		alert.addButton(withTitle: tr("Cancel"))
		alert.layout()
		alert.window.initialFirstResponder = box
		guard alert.runModal() == .alertFirstButtonReturn else { return nil }
		return box.indexOfSelectedItem
	}

	/// Text typed in a dialog, or nil when cancelled.
	static func askText(_ message: String, _ title: String, value: String = "", maxLength: Int = Model.maxName) -> String? {
		let alert = NSAlert()
		alert.messageText = title
		alert.informativeText = message
		let field = TextField(label: accessibleName(message), width: 320)
		field.frame = NSRect(x: 0, y: 0, width: 320, height: 24)
		field.stringValue = value
		field.maxLength = maxLength
		alert.accessoryView = field
		alert.addButton(withTitle: "OK")
		alert.addButton(withTitle: tr("Cancel"))
		alert.layout()
		alert.window.initialFirstResponder = field
		guard alert.runModal() == .alertFirstButtonReturn else { return nil }
		return String(field.stringValue.prefix(maxLength))
	}

	/// Yes or No, with No as the default answer.
	static func confirm(_ message: String, _ title: String) -> Bool {
		let alert = NSAlert()
		alert.alertStyle = .warning
		alert.messageText = title
		alert.informativeText = message
		let no = alert.addButton(withTitle: tr("No"))
		no.keyEquivalent = "\r"
		let yes = alert.addButton(withTitle: tr("Yes"))
		yes.keyEquivalent = ""
		return alert.runModal() == .alertSecondButtonReturn
	}

	static func message(_ text: String, _ title: String = Messages.appName) {
		let alert = NSAlert()
		alert.alertStyle = .warning
		alert.messageText = title
		alert.informativeText = text
		alert.addButton(withTitle: "OK")
		alert.runModal()
	}
}

/// Target of the items of Prompts.chooseFromMenu.
final class MenuPicker: NSObject {
	var chosen: Int?

	@objc func pick(_ sender: NSMenuItem) {
		chosen = sender.tag
	}
}
