// swift-tools-version:5.9
// Notas Workflow Mac - the macOS version of the NVDA add-on NotasWorkflowNVDA.
// Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
// This file is covered by the GNU General Public License, version 2.

import PackageDescription

let package = Package(
	name: "NotasWorkflowMac",
	platforms: [.macOS(.v13)],
	products: [
		.executable(name: "NotasWorkflowMac", targets: ["NotasWorkflowMac"]),
	],
	targets: [
		// Notes, notebooks, folders, file, markup and search. No AppKit here (tested by NotasSelfTest).
		.target(name: "NotasCore"),
		// The app: windows, global shortcuts and VoiceOver announcements.
		.executableTarget(name: "NotasWorkflowMac", dependencies: ["NotasCore"]),
		// Self tests of NotasCore: `swift run NotasSelfTest` (works with only the Command Line Tools).
		.executableTarget(name: "NotasSelfTest", dependencies: ["NotasCore"]),
	]
)
