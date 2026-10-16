// Notas Workflow Mac - TreeView.swift
// The trees of the windows (lanes and notes; folders, notebooks and notes) on top of a
// native NSOutlineView, which VoiceOver reads as an outline: "To do, 3 notes, collapsed,
// level 1". Right Arrow opens a branch and Left Arrow closes it.
// Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
// This file is covered by the GNU General Public License, version 2.

import AppKit

/// What an item of a tree is, like the data of the tree items in the add-on:
/// ("lane", id), ("note", id), ("more", lane), ("folder", id), ("notebook", id), ("none", nil), ("loose", nil).
struct NodeKey: Hashable {
	let kind: String
	let ident: String?

	init(_ kind: String, _ ident: String? = nil) {
		self.kind = kind
		self.ident = ident
	}
}

final class TreeNode {
	let key: NodeKey
	var text: String
	var children: [TreeNode] = []
	weak var parent: TreeNode?
	/// The node can be opened even before its children are added (they are added when it opens).
	var hasChildren = false
	/// For "Show more notes" items: the branch they belong to.
	var moreOf: NodeKey?

	init(_ key: NodeKey, _ text: String) {
		self.key = key
		self.text = text
	}

	@discardableResult
	func append(_ node: TreeNode) -> TreeNode {
		node.parent = self
		children.append(node)
		return node
	}
}

final class TreeView: NSObject, NSOutlineViewDataSource, NSOutlineViewDelegate {
	let outline = NSOutlineView()
	let scroll = NSScrollView()
	var roots: [TreeNode] = []
	/// Enter and double click.
	var onActivate: (() -> Void)?
	var onSelectionChange: (() -> Void)?
	/// A branch was opened (true) or closed (false).
	var onExpanded: ((TreeNode, Bool) -> Void)?
	/// A branch is about to open: its children can be added now.
	var onWillExpand: ((TreeNode) -> Void)?
	private static let cellId = NSUserInterfaceItemIdentifier("cell")

	init(label: String, width: CGFloat, height: CGFloat) {
		super.init()
		let column = NSTableColumn(identifier: NSUserInterfaceItemIdentifier("text"))
		column.resizingMask = .autoresizingMask
		outline.addTableColumn(column)
		outline.outlineTableColumn = column
		outline.headerView = nil
		outline.allowsMultipleSelection = false
		outline.allowsEmptySelection = true
		outline.autoresizesOutlineColumn = true
		outline.columnAutoresizingStyle = .uniformColumnAutoresizingStyle
		outline.usesAutomaticRowHeights = false
		outline.rowHeight = 20
		outline.dataSource = self
		outline.delegate = self
		outline.target = self
		outline.doubleAction = #selector(doubleClicked)
		outline.setAccessibilityLabel(label)
		scroll.documentView = outline
		scroll.hasVerticalScroller = true
		scroll.borderType = .bezelBorder
		scroll.translatesAutoresizingMaskIntoConstraints = false
		scroll.widthAnchor.constraint(greaterThanOrEqualToConstant: width).isActive = true
		scroll.heightAnchor.constraint(greaterThanOrEqualToConstant: height).isActive = true
	}

	@objc func doubleClicked() {
		if outline.clickedRow >= 0 {
			onActivate?()
		}
	}

	/// Shows the roots again (the nodes are new objects).
	func reload() {
		outline.reloadData()
	}

	/// Shows the new children of a node.
	func reload(_ node: TreeNode) {
		outline.reloadItem(node, reloadChildren: true)
	}

	func setText(_ node: TreeNode, _ text: String) {
		node.text = text
		outline.reloadItem(node, reloadChildren: false)
	}

	var selected: TreeNode? {
		let row = outline.selectedRow
		return row >= 0 ? outline.item(atRow: row) as? TreeNode : nil
	}

	func isExpanded(_ node: TreeNode) -> Bool {
		outline.isItemExpanded(node)
	}

	func expand(_ node: TreeNode) {
		outline.expandItem(node)
	}

	func toggle(_ node: TreeNode) {
		if outline.isItemExpanded(node) {
			outline.collapseItem(node)
		} else {
			outline.expandItem(node)
		}
	}

	/// Selects a node, opening its branch, and shows it.
	func select(_ node: TreeNode) {
		var chain: [TreeNode] = []
		var p = node.parent
		while let parent = p {
			chain.insert(parent, at: 0)
			p = parent.parent
		}
		for parent in chain where !outline.isItemExpanded(parent) {
			outline.expandItem(parent)
		}
		let row = outline.row(forItem: node)
		if row >= 0 {
			outline.selectRowIndexes(IndexSet(integer: row), byExtendingSelection: false)
			outline.scrollRowToVisible(row)
		}
	}

	// MARK: data source

	func outlineView(_ outlineView: NSOutlineView, numberOfChildrenOfItem item: Any?) -> Int {
		guard let node = item as? TreeNode else { return roots.count }
		return node.children.count
	}

	func outlineView(_ outlineView: NSOutlineView, child index: Int, ofItem item: Any?) -> Any {
		guard let node = item as? TreeNode else { return roots[index] }
		return node.children[index]
	}

	func outlineView(_ outlineView: NSOutlineView, isItemExpandable item: Any) -> Bool {
		guard let node = item as? TreeNode else { return false }
		return node.hasChildren || !node.children.isEmpty
	}

	func outlineView(_ outlineView: NSOutlineView, viewFor tableColumn: NSTableColumn?, item: Any) -> NSView? {
		guard let node = item as? TreeNode else { return nil }
		let cell: NSTableCellView
		if let reused = outlineView.makeView(withIdentifier: Self.cellId, owner: nil) as? NSTableCellView {
			cell = reused
		} else {
			cell = NSTableCellView()
			cell.identifier = Self.cellId
			let text = NSTextField(labelWithString: "")
			text.lineBreakMode = .byTruncatingTail
			text.translatesAutoresizingMaskIntoConstraints = false
			cell.addSubview(text)
			cell.textField = text
			NSLayoutConstraint.activate([
				text.leadingAnchor.constraint(equalTo: cell.leadingAnchor, constant: 2),
				text.trailingAnchor.constraint(equalTo: cell.trailingAnchor, constant: -2),
				text.centerYAnchor.constraint(equalTo: cell.centerYAnchor),
			])
		}
		cell.textField?.stringValue = node.text
		return cell
	}

	// MARK: delegate

	func outlineView(_ outlineView: NSOutlineView, shouldExpandItem item: Any) -> Bool {
		if let node = item as? TreeNode {
			onWillExpand?(node)
		}
		return true
	}

	func outlineViewItemDidExpand(_ notification: Notification) {
		if let node = notification.userInfo?["NSObject"] as? TreeNode {
			onExpanded?(node, true)
		}
	}

	func outlineViewItemDidCollapse(_ notification: Notification) {
		if let node = notification.userInfo?["NSObject"] as? TreeNode {
			onExpanded?(node, false)
		}
	}

	func outlineViewSelectionDidChange(_ notification: Notification) {
		onSelectionChange?()
	}
}
