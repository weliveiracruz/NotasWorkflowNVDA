# -*- coding: UTF-8 -*-
"""Shared helpers: loads the add-on core (model, markup, search, store) without NVDA."""

import importlib
import os
import sys
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
PKG_DIR = os.path.join(ROOT, "addon", "globalPlugins", "NotasWorkflowNVDA")
sys.path.insert(0, HERE)

CORE = ("model", "markup", "search", "store", "exporter")


def loadCore():
	"""Imports the core modules as package 'NotasWorkflowNVDA' without running its
	__init__ (which needs NVDA). Returns a namespace with the modules."""
	if "NotasWorkflowNVDA" not in sys.modules:
		pkg = types.ModuleType("NotasWorkflowNVDA")
		pkg.__path__ = [PKG_DIR]
		sys.modules["NotasWorkflowNVDA"] = pkg
	ns = types.SimpleNamespace()
	for name in CORE:
		setattr(ns, name, importlib.import_module("NotasWorkflowNVDA." + name))
	return ns


def tempFolder():
	return tempfile.mkdtemp(prefix="notasworkflownvda-test-")


def newStore(core, folder=None):
	s = core.store.NotesStore(folder or tempFolder())
	s.load()
	return s
