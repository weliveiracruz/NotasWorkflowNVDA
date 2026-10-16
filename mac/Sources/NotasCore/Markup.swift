// Notas Workflow Mac - Markup.swift
// The note content is stored as HTML (paragraphs, headings, lists, quotes), the same HTML
// of the web app and of the NVDA add-on. Here it is edited as plain text with a light
// markup, converted both ways without loss. Port of markup.py.
// Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
// This file is covered by the GNU General Public License, version 2.

import Foundation

final class Rx {
	let re: NSRegularExpression

	init(_ pattern: String, _ options: NSRegularExpression.Options = []) {
		re = try! NSRegularExpression(pattern: pattern, options: options)
	}

	/// Groups of a match of the whole text (nil when it does not match). Missing groups are "".
	func match(_ text: String) -> [String]? {
		let ns = text as NSString
		guard let m = re.firstMatch(in: text, range: NSRange(location: 0, length: ns.length)) else { return nil }
		return (0..<m.numberOfRanges).map { i in
			let r = m.range(at: i)
			return r.location == NSNotFound ? "" : ns.substring(with: r)
		}
	}

	func matches(_ text: String) -> Bool {
		re.firstMatch(in: text, range: NSRange(location: 0, length: (text as NSString).length)) != nil
	}

	func replace(_ text: String, _ template: String) -> String {
		re.stringByReplacingMatches(in: text, range: NSRange(location: 0, length: (text as NSString).length), withTemplate: template)
	}

	func replaceFirst(_ text: String, _ with: String) -> String {
		let ns = text as NSString
		guard let m = re.firstMatch(in: text, range: NSRange(location: 0, length: ns.length)) else { return text }
		return ns.replacingCharacters(in: m.range, with: with)
	}
}

public enum Markup {
	static let headingRe = Rx("^(#{1,6}) (.*)$")
	static let bulletRe = Rx("^[-*] (.*)$")
	static let orderedRe = Rx("^(\\d{1,9})\\. (.*)$")
	static let quoteRe = Rx("^> ?(.*)$")
	static let ruleRe = Rx("^-{3,}$")
	static let fence = "```"

	static let codeSpanRe = Rx("`([^`]+)`")
	static let boldRe = Rx("\\*\\*(?=\\S)(.+?)(?<=\\S)\\*\\*")
	static let strikeRe = Rx("~~(?=\\S)(.+?)(?<=\\S)~~")
	// * only marks italics at the start and end of words: 2*3*4 stays as it is.
	static let italicRe = Rx("(?<![\\w*])\\*(?=[^\\s*])(.+?)(?<=[^\\s*])\\*(?![\\w*])")

	/// html.escape(text, quote=False)
	static func escape(_ text: String) -> String {
		var out = ""
		out.reserveCapacity(text.utf8.count)
		for ch in text {
			switch ch {
			case "&": out += "&amp;"
			case "<": out += "&lt;"
			case ">": out += "&gt;"
			default: out.append(ch)
			}
		}
		return out
	}

	/// Escapes the text and turns the inline markup into HTML.
	static func inline(_ text: String) -> String {
		let ns = text as NSString
		var out = ""
		var pos = 0
		for m in codeSpanRe.re.matches(in: text, range: NSRange(location: 0, length: ns.length)) {
			out += emphasis(ns.substring(with: NSRange(location: pos, length: m.range.location - pos)))
			out += "<code>" + escape(ns.substring(with: m.range(at: 1))) + "</code>"
			pos = m.range.location + m.range.length
		}
		out += emphasis(ns.substring(from: pos))
		return out
	}

	static func emphasis(_ text: String) -> String {
		var t = escape(text)
		t = boldRe.replace(t, "<strong>$1</strong>")
		t = strikeRe.replace(t, "<s>$1</s>")
		return italicRe.replace(t, "<em>$1</em>")
	}

	static func splitLines(_ text: String) -> [String] {
		text.replacingOccurrences(of: "\r\n", with: "\n").replacingOccurrences(of: "\r", with: "\n").components(separatedBy: "\n")
	}

	/// Light markup (what the editor shows) -> HTML (what is stored).
	public static func textToHtml(_ text: String) -> String {
		if text.isEmpty {
			return ""
		}
		let lines = splitLines(text)
		var out: [String] = []
		var i = 0
		while i < lines.count {
			let line = lines[i]
			let stripped = line.trimmingCharacters(in: .whitespacesAndNewlines)
			if stripped == fence {
				var code: [String] = []
				i += 1
				while i < lines.count && lines[i].trimmingCharacters(in: .whitespacesAndNewlines) != fence {
					code.append(lines[i])
					i += 1
				}
				i += 1
				out.append("<pre><code>" + escape(code.joined(separator: "\n")) + "</code></pre>")
				continue
			}
			if ruleRe.matches(stripped) {
				out.append("<hr>")
				i += 1
				continue
			}
			if let m = headingRe.match(line) {
				let level = m[1].count
				out.append("<h\(level)>" + inline(m[2]) + "</h\(level)>")
				i += 1
				continue
			}
			if bulletRe.matches(line) {
				var items = ""
				while i < lines.count, let m = bulletRe.match(lines[i]) {
					items += "<li><p>" + inline(m[1]) + "</p></li>"
					i += 1
				}
				out.append("<ul>" + items + "</ul>")
				continue
			}
			if let m = orderedRe.match(line) {
				let start = Int(m[1]) ?? 1
				var items = ""
				while i < lines.count, let mm = orderedRe.match(lines[i]) {
					items += "<li><p>" + inline(mm[2]) + "</p></li>"
					i += 1
				}
				let attr = start != 1 ? " start=\"\(start)\"" : ""
				out.append("<ol\(attr)>" + items + "</ol>")
				continue
			}
			if quoteRe.matches(line) {
				var paras = ""
				while i < lines.count, let m = quoteRe.match(lines[i]) {
					paras += m[1].isEmpty ? "<p></p>" : "<p>" + inline(m[1]) + "</p>"
					i += 1
				}
				out.append("<blockquote>" + paras + "</blockquote>")
				continue
			}
			out.append(line.isEmpty ? "<p></p>" : "<p>" + inline(line) + "</p>")
			i += 1
		}
		return out.joined()
	}

	// MARK: HTML -> text

	/// Stored HTML -> light markup (shown in the editor).
	public static func htmlToText(_ content: String) -> String {
		convert(content, plain: false)
	}

	/// Only the words of the note, without markup.
	public static func plainText(_ content: String) -> String {
		convert(content, plain: true)
	}

	/// One line with the first characters of the note.
	public static func preview(_ content: String, limit: Int = 100) -> String {
		let text = plainText(content).split(whereSeparator: { $0.isWhitespace }).joined(separator: " ")
		return String(text.prefix(limit))
	}

	static func convert(_ content: String, plain: Bool) -> String {
		if content.isEmpty {
			return ""
		}
		if !content.contains("<") {
			// Plain text (for example, imported from another tool).
			return HTMLEntities.unescape(content).replacingOccurrences(of: "\r\n", with: "\n")
		}
		let conv = HTMLConverter(plain: plain)
		HTMLTokenizer.parse(content, conv)
		return conv.result()
	}

	// MARK: formatting of the editor

	public static let inlineMarks = ["bold": "**", "italic": "*", "strike": "~~", "code": "`"]
	public static let linePrefixes = ["heading2": "## ", "heading3": "### ", "bullet": "- ", "ordered": "1. ", "quote": "> "]
	static let linePrefixRe: [String: Rx] = [
		"heading2": Rx("^## "),
		"heading3": Rx("^### "),
		"bullet": Rx("^[-*] "),
		"ordered": Rx("^\\d{1,9}\\. "),
		"quote": Rx("^> ?"),
	]
	static let anyHeadingRe = Rx("^#{1,6} ")
	public static let formats = ["bold", "italic", "strike", "code", "heading2", "heading3", "bullet", "ordered", "quote", "divider"]

	/// Applies (or removes) a format to the selection [start, end) of text. Positions are
	/// UTF-16 offsets, as NSTextView uses. Returns (newText, newStart, newEnd, applied):
	/// applied is false when the format was removed.
	public static func applyFormat(_ text: String, _ start: Int, _ end: Int, _ kind: String) -> (String, Int, Int, Bool) {
		let ns = text as NSString
		let a = max(0, min(start, ns.length))
		let b = max(0, min(end, ns.length))
		let s = min(a, b)
		let e = max(a, b)
		if let mark = inlineMarks[kind] {
			return inlineFormat(ns, s, e, mark)
		}
		if linePrefixes[kind] != nil {
			return lineFormat(ns, s, e, kind)
		}
		// divider
		let before = (s == 0 || ns.substring(with: NSRange(location: s - 1, length: 1)) == "\n") ? "" : "\n"
		let after = (e < ns.length && ns.substring(with: NSRange(location: e, length: 1)) == "\n") ? "" : "\n"
		let insert = before + "---" + after
		let pos = s + (insert as NSString).length
		let new = ns.substring(to: s) + insert + ns.substring(from: e)
		return (new, pos, pos, true)
	}

	static func inlineFormat(_ ns: NSString, _ start: Int, _ end: Int, _ mark: String) -> (String, Int, Int, Bool) {
		let size = (mark as NSString).length
		if start == end {
			let new = ns.substring(to: start) + mark + mark + ns.substring(from: end)
			return (new, start + size, start + size, true)
		}
		let sel = ns.substring(with: NSRange(location: start, length: end - start))
		let selLen = (sel as NSString).length
		if selLen > 2 * size && sel.hasPrefix(mark) && sel.hasSuffix(mark) {
			let inner = (sel as NSString).substring(with: NSRange(location: size, length: selLen - 2 * size))
			return (ns.substring(to: start) + inner + ns.substring(from: end), start, start + (inner as NSString).length, false)
		}
		let beforeStart = max(0, start - size)
		let markBefore = ns.substring(with: NSRange(location: beforeStart, length: start - beforeStart))
		let markAfter = ns.substring(with: NSRange(location: end, length: min(size, ns.length - end)))
		if markBefore == mark && markAfter == mark {
			return (ns.substring(to: start - size) + sel + ns.substring(from: end + size), start - size, end - size, false)
		}
		return (ns.substring(to: start) + mark + sel + mark + ns.substring(from: end), start + size, end + size, true)
	}

	static func lineFormat(_ ns: NSString, _ start: Int, _ end: Int, _ kind: String) -> (String, Int, Int, Bool) {
		let found = ns.range(of: "\n", options: .backwards, range: NSRange(location: 0, length: start))
		let lineStart = found.location == NSNotFound ? 0 : found.location + 1
		let next = ns.range(of: "\n", options: [], range: NSRange(location: end, length: ns.length - end))
		let lineEnd = next.location == NSNotFound ? ns.length : next.location
		let lines = ns.substring(with: NSRange(location: lineStart, length: lineEnd - lineStart)).components(separatedBy: "\n")
		let pattern = linePrefixRe[kind]!
		let remove = lines.allSatisfy { pattern.matches($0) }
		var out: [String] = []
		for (n, original) in lines.enumerated() {
			var line = original
			if remove {
				out.append(pattern.replaceFirst(line, ""))
				continue
			}
			if kind.hasPrefix("heading") {
				line = anyHeadingRe.replaceFirst(line, "")
			} else if pattern.matches(line) {
				line = pattern.replaceFirst(line, "")
			}
			let prefix = kind == "ordered" ? "\(n + 1). " : linePrefixes[kind]!
			out.append(prefix + line)
		}
		let segment = out.joined(separator: "\n")
		let new = ns.substring(to: lineStart) + segment + ns.substring(from: lineEnd)
		if start == end {
			let pos = lineStart + (out[0] as NSString).length
			return (new, pos, pos, !remove)
		}
		return (new, lineStart, lineStart + (segment as NSString).length, !remove)
	}
}

// MARK: - HTML reading

protocol HTMLHandler: AnyObject {
	func startTag(_ tag: String, _ attrs: [(String, String)], selfClosing: Bool)
	func endTag(_ tag: String)
	func data(_ text: String)
}

/// A small HTML tokenizer (what html.parser does for the content of the notes): tags,
/// attributes, comments and text with entities. It never runs anything.
enum HTMLTokenizer {
	static func parse(_ html: String, _ handler: HTMLHandler) {
		let s = Array(html.unicodeScalars)
		var i = 0
		var text = String.UnicodeScalarView()
		var rawTextEnd: String?

		func flushText() {
			if !text.isEmpty {
				handler.data(HTMLEntities.unescape(String(text)))
				text = String.UnicodeScalarView()
			}
		}

		func isLetter(_ c: Unicode.Scalar) -> Bool {
			(c.value >= 65 && c.value <= 90) || (c.value >= 97 && c.value <= 122)
		}

		while i < s.count {
			let c = s[i]
			if let end = rawTextEnd {
				// Inside script or style: everything up to the closing tag is text.
				let closing = Array(("</" + end).unicodeScalars)
				var j = i
				var found = -1
				while j + closing.count <= s.count {
					var ok = true
					for k in 0..<closing.count where String(s[j + k]).lowercased() != String(closing[k]) {
						ok = false
						break
					}
					if ok {
						found = j
						break
					}
					j += 1
				}
				let stop = found == -1 ? s.count : found
				var chunk = String.UnicodeScalarView()
				chunk.append(contentsOf: s[i..<stop])
				handler.data(String(chunk))
				i = stop
				rawTextEnd = nil
				continue
			}
			if c == "<" && i + 1 < s.count {
				let n = s[i + 1]
				if n == "!" {
					flushText()
					// Comment or doctype: skipped.
					if i + 3 < s.count && s[i + 2] == "-" && s[i + 3] == "-" {
						// "<!-->" and "<!--->" are complete (empty) comments too.
						var j = i + 2
						while j + 2 < s.count && !(s[j] == "-" && s[j + 1] == "-" && s[j + 2] == ">") {
							j += 1
						}
						i = min(s.count, j + 3)
					} else {
						var j = i + 2
						while j < s.count && s[j] != ">" { j += 1 }
						i = min(s.count, j + 1)
					}
					continue
				}
				if isLetter(n) || (n == "/" && i + 2 < s.count && isLetter(s[i + 2])) {
					// Finds the end of the tag. As in html.parser, quotes only delimit a value
					// right after "=".
					var j = i + 1
					var quote: Unicode.Scalar?
					var afterEquals = false
					while j < s.count {
						let d = s[j]
						if let q = quote {
							if d == q { quote = nil }
						} else if afterEquals && (d == "\"" || d == "'") {
							afterEquals = false
							if s[(j + 1)...].contains(d) {
								quote = d
							} else if s[j - 1] == "=" {
								// html.parser: a quote right after "=" that never closes leaves the
								// tag unfinished (and then dropped).
								j = s.count
								break
							}
							// Otherwise the quote is just part of a name.
						} else if d == ">" {
							break
						} else if d == "=" {
							afterEquals = true
						} else if !CharacterSet.whitespacesAndNewlines.contains(d) {
							afterEquals = false
						}
						j += 1
					}
					if j >= s.count {
						// A tag not closed at the end of the content is dropped, as html.parser does.
						flushText()
						i = s.count
						continue
					}
					flushText()
					var inner = String.UnicodeScalarView()
					inner.append(contentsOf: s[(i + 1)..<j])
					i = j + 1
					let tagText = String(inner)
					if tagText.hasPrefix("/") {
						let name = tagText.dropFirst().trimmingCharacters(in: .whitespaces).split(separator: " ").first.map { String($0).lowercased() } ?? ""
						if !name.isEmpty {
							handler.endTag(name)
						}
					} else {
						let (name, attrs, selfClosing) = parseTag(tagText)
						handler.startTag(name, attrs, selfClosing: selfClosing)
						if !selfClosing && (name == "script" || name == "style") {
							rawTextEnd = name
						}
					}
					continue
				}
			}
			text.append(c)
			i += 1
		}
		flushText()
	}

	static func parseTag(_ body: String) -> (String, [(String, String)], Bool) {
		var t = body
		var selfClosing = false
		if t.hasSuffix("/") {
			selfClosing = true
			t.removeLast()
		}
		let s = Array(t.unicodeScalars)
		var i = 0
		var name = String.UnicodeScalarView()
		while i < s.count && !CharacterSet.whitespacesAndNewlines.contains(s[i]) && s[i] != "/" {
			name.append(s[i])
			i += 1
		}
		var attrs: [(String, String)] = []
		while i < s.count {
			while i < s.count && (CharacterSet.whitespacesAndNewlines.contains(s[i]) || s[i] == "/") { i += 1 }
			var key = String.UnicodeScalarView()
			while i < s.count && !CharacterSet.whitespacesAndNewlines.contains(s[i]) && s[i] != "=" && s[i] != "/" {
				key.append(s[i])
				i += 1
			}
			while i < s.count && CharacterSet.whitespacesAndNewlines.contains(s[i]) { i += 1 }
			var value = String.UnicodeScalarView()
			if i < s.count && s[i] == "=" {
				i += 1
				while i < s.count && CharacterSet.whitespacesAndNewlines.contains(s[i]) { i += 1 }
				if i < s.count && (s[i] == "\"" || s[i] == "'") {
					let q = s[i]
					i += 1
					while i < s.count && s[i] != q {
						value.append(s[i])
						i += 1
					}
					i += 1
				} else {
					while i < s.count && !CharacterSet.whitespacesAndNewlines.contains(s[i]) {
						value.append(s[i])
						i += 1
					}
				}
			}
			if !key.isEmpty {
				attrs.append((String(key).lowercased(), HTMLEntities.unescape(String(value))))
			}
		}
		return (String(name).lowercased(), attrs, selfClosing)
	}
}

public enum HTMLEntities {
	static let named: [String: String] = [
		"amp": "&", "lt": "<", "gt": ">", "quot": "\"", "apos": "'", "nbsp": "\u{00A0}",
		"ndash": "–", "mdash": "—", "hellip": "…", "lsquo": "‘", "rsquo": "’", "ldquo": "“", "rdquo": "”",
		"laquo": "«", "raquo": "»", "bull": "•", "middot": "·", "copy": "©", "reg": "®", "trade": "™",
		"deg": "°", "euro": "€", "times": "×", "divide": "÷", "shy": "\u{00AD}",
		"aacute": "á", "Aacute": "Á", "agrave": "à", "Agrave": "À", "acirc": "â", "Acirc": "Â", "atilde": "ã", "Atilde": "Ã",
		"auml": "ä", "eacute": "é", "Eacute": "É", "egrave": "è", "ecirc": "ê", "Ecirc": "Ê", "iacute": "í", "Iacute": "Í",
		"oacute": "ó", "Oacute": "Ó", "ocirc": "ô", "Ocirc": "Ô", "otilde": "õ", "Otilde": "Õ", "ouml": "ö",
		"uacute": "ú", "Uacute": "Ú", "uuml": "ü", "Uuml": "Ü", "ccedil": "ç", "Ccedil": "Ç", "ntilde": "ñ", "Ntilde": "Ñ",
	]

	/// html.unescape for the entities used in notes: numeric ones and the common named ones.
	public static func unescape(_ text: String) -> String {
		guard text.contains("&") else { return text }
		var out = ""
		var rest = Substring(text)
		while let amp = rest.firstIndex(of: "&") {
			out += rest[rest.startIndex..<amp]
			let after = rest[rest.index(after: amp)...]
			if let semi = after.prefix(32).firstIndex(of: ";") {
				let name = String(after[after.startIndex..<semi])
				var replacement: String?
				if name.hasPrefix("#x") || name.hasPrefix("#X") {
					replacement = UInt32(name.dropFirst(2), radix: 16).flatMap(scalar)
				} else if name.hasPrefix("#") {
					replacement = UInt32(name.dropFirst(1)).flatMap(scalar)
				} else {
					replacement = named[name]
				}
				if let replacement {
					out += replacement
					rest = after[after.index(after: semi)...]
					continue
				}
			}
			out += "&"
			rest = after
		}
		out += rest
		return out
	}

	static func scalar(_ value: UInt32) -> String? {
		if value == 0 || (value >= 0xD800 && value <= 0xDFFF) || value > 0x10FFFF {
			return "\u{FFFD}"
		}
		return Unicode.Scalar(value).map { String(Character($0)) }
	}
}

/// Stored HTML -> light markup (plain=false) or text only (plain=true).
/// Unknown tags become just their text; script and style are dropped.
final class HTMLConverter: HTMLHandler {
	static let marks = ["strong": "**", "b": "**", "em": "*", "i": "*", "s": "~~", "strike": "~~", "del": "~~"]
	static let skipTags: Set<String> = ["script", "style", "template", "head", "title", "iframe", "object", "noscript"]

	let plain: Bool
	var lines: [String] = []
	var buf: [String] = []
	var prefix = ""
	var lists: [(String, Int)] = []
	var quote = 0
	var pre = false
	var skip = 0

	init(plain: Bool) {
		self.plain = plain
	}

	static func headingLevel(_ tag: String) -> Int? {
		let c = Array(tag)
		if c.count == 2 && c[0] == "h", let n = Int(String(c[1])), (1...6).contains(n) {
			return n
		}
		return nil
	}

	func emit() {
		let q = plain ? "" : String(repeating: "> ", count: quote)
		lines.append(q + prefix + buf.joined())
		buf = []
		prefix = ""
	}

	func flush() {
		if !buf.isEmpty {
			emit()
		}
	}

	func mark(_ text: String) {
		if !plain {
			buf.append(text)
		}
	}

	func emitRaw(_ text: String) {
		let q = plain ? "" : String(repeating: "> ", count: quote)
		lines.append(q + text)
	}

	func startTag(_ tag: String, _ attrs: [(String, String)], selfClosing: Bool) {
		handleStart(tag, attrs)
		if selfClosing && tag != "br" && tag != "hr" {
			endTag(tag)
		}
	}

	func handleStart(_ tag: String, _ attrs: [(String, String)]) {
		if Self.skipTags.contains(tag) {
			skip += 1
			return
		}
		if skip > 0 {
			return
		}
		if tag == "p" || tag == "div" {
			flush()
		} else if let level = Self.headingLevel(tag) {
			flush()
			mark(String(repeating: "#", count: level) + " ")
		} else if tag == "ul" || tag == "ol" {
			flush()
			var start = 1
			for (name, value) in attrs where name == "start" {
				if !value.isEmpty && value.count < 10 && value.allSatisfy({ $0.isASCII && $0.isNumber }), let n = Int(value) {
					start = n
				}
			}
			lists.append((tag, start - 1))
		} else if tag == "li" {
			flush()
			if !lists.isEmpty && !plain {
				let indent = String(repeating: "  ", count: lists.count - 1)
				if lists[lists.count - 1].0 == "ol" {
					lists[lists.count - 1].1 += 1
					prefix = "\(indent)\(lists[lists.count - 1].1). "
				} else {
					prefix = indent + "- "
				}
			}
		} else if tag == "blockquote" {
			flush()
			quote += 1
		} else if tag == "pre" {
			flush()
			if !plain {
				emitRaw(Markup.fence)
			}
			pre = true
		} else if tag == "hr" {
			flush()
			if !plain {
				emitRaw("---")
			}
		} else if tag == "br" {
			emit()
		} else if let m = Self.marks[tag] {
			mark(m)
		} else if tag == "code" && !pre {
			mark("`")
		}
	}

	func endTag(_ tag: String) {
		if Self.skipTags.contains(tag) {
			skip = max(0, skip - 1)
			return
		}
		if skip > 0 {
			return
		}
		if tag == "p" || tag == "div" || Self.headingLevel(tag) != nil {
			emit()
		} else if tag == "li" {
			if !buf.isEmpty || !prefix.isEmpty {
				emit()
			}
		} else if tag == "ul" || tag == "ol" {
			flush()
			if !lists.isEmpty {
				lists.removeLast()
			}
		} else if tag == "blockquote" {
			flush()
			quote = max(0, quote - 1)
		} else if tag == "pre" {
			flush()
			if !plain {
				emitRaw(Markup.fence)
			}
			pre = false
		} else if let m = Self.marks[tag] {
			mark(m)
		} else if tag == "code" && !pre {
			mark("`")
		}
	}

	func data(_ text: String) {
		if skip > 0 {
			return
		}
		if pre {
			let parts = text.replacingOccurrences(of: "\r\n", with: "\n").components(separatedBy: "\n")
			for (n, part) in parts.enumerated() {
				if n > 0 {
					emit()
				}
				buf.append(part)
			}
			return
		}
		buf.append(text.replacingOccurrences(of: "\r", with: " ").replacingOccurrences(of: "\n", with: " ").replacingOccurrences(of: "\t", with: " "))
	}

	func result() -> String {
		flush()
		return lines.joined(separator: "\n")
	}
}
