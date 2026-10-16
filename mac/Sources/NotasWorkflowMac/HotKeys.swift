// Notas Workflow Mac - HotKeys.swift
// Global shortcuts that work in any app, like the NVDA+Alt+N, F and B gestures of the add-on.
// Carbon's RegisterEventHotKey needs no Accessibility permission.
// Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
// This file is covered by the GNU General Public License, version 2.

import Carbon.HIToolbox

enum HotKeys {
	private static var actions: [UInt32: () -> Void] = [:]
	private static var refs: [EventHotKeyRef] = []
	private static var installed = false
	private static let signature: OSType = 0x4E_57_4D_43 // "NWMC"

	/// Option+Shift+Command and a key (kVK_ANSI_N, kVK_ANSI_F, kVK_ANSI_B...).
	static let modifiers = UInt32(optionKey | shiftKey | cmdKey)

	static func register(keyCode: Int, modifiers: UInt32 = HotKeys.modifiers, action: @escaping () -> Void) {
		installHandler()
		let id = UInt32(actions.count + 1)
		actions[id] = action
		var ref: EventHotKeyRef?
		let status = RegisterEventHotKey(UInt32(keyCode), modifiers, EventHotKeyID(signature: signature, id: id), GetApplicationEventTarget(), 0, &ref)
		if status == noErr, let ref {
			refs.append(ref)
		}
	}

	private static func installHandler() {
		if installed {
			return
		}
		installed = true
		var spec = EventTypeSpec(eventClass: OSType(kEventClassKeyboard), eventKind: UInt32(kEventHotKeyPressed))
		InstallEventHandler(GetApplicationEventTarget(), { _, event, _ -> OSStatus in
			var hotKey = EventHotKeyID()
			let status = GetEventParameter(event, EventParamName(kEventParamDirectObject), EventParamType(typeEventHotKeyID), nil, MemoryLayout<EventHotKeyID>.size, nil, &hotKey)
			if status == noErr, let action = HotKeys.actions[hotKey.id] {
				DispatchQueue.main.async(execute: action)
			}
			return noErr
		}, 1, &spec, nil, nil)
	}
}
