# -*- coding: UTF-8 -*-
"""Finds every translatable string (_("...")) of the add-on, with the
Translators comment that comes right before it.

Usage:  python tests/_strings.py   prints a .pot file (to start a translation)."""

import ast
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
ADDON = os.path.join(ROOT, "addon")


def addonFiles():
	for folder, dirs, files in os.walk(ADDON):
		dirs[:] = sorted(d for d in dirs if d != "__pycache__")
		for name in sorted(files):
			if name.endswith(".py"):
				yield os.path.join(folder, name)


def translatable():
	"""Returns a list of (file, line, msgid, hasTranslatorsComment)."""
	out = []
	for path in addonFiles():
		with open(path, encoding="utf-8") as f:
			source = f.read()
		lines = source.splitlines()
		for node in ast.walk(ast.parse(source)):
			if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_" and node.args:
				arg = node.args[0]
				if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
					previous = lines[node.lineno - 2].strip() if node.lineno >= 2 else ""
					out.append((os.path.relpath(path, ROOT), node.lineno, arg.value, previous.startswith("# Translators:")))
	return out


def _quote(s):
	return '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


if __name__ == "__main__":
	seen = {}
	for path, line, msgid, _ok in translatable():
		seen.setdefault(msgid, []).append("%s:%d" % (path, line))
	print('msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n')
	for msgid, refs in seen.items():
		print("#: %s\nmsgid %s\nmsgstr \"\"\n" % (" ".join(refs), _quote(msgid)))
