# -*- coding: UTF-8 -*-
"""Small helper shared by the check-style test suites: records each check and
prints one machine-readable RESULT line read by tests/run_all.py."""

import json
import sys


class Recorder:
	def __init__(self, suite):
		self.suite = suite
		self.results = []  # (name, ok, info)

	def check(self, name, ok, info=""):
		ok = bool(ok)
		self.results.append((name, ok, info))
		print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  -> %s" % (info,)))
		sys.stdout.flush()
		return ok

	def finish(self):
		failed = [n for n, ok, _i in self.results if not ok]
		print("\n%d checks, %d failed" % (len(self.results), len(failed)))
		print("RESULT " + json.dumps({
			"suite": self.suite,
			"total": len(self.results),
			"passed": len(self.results) - len(failed),
			"failed": len(failed),
			"failures": failed,
			"tests": [n for n, _ok, _i in self.results],
		}, ensure_ascii=False))
		sys.stdout.flush()
		return 1 if failed else 0


def emit(suite, names, failures):
	"""RESULT line for suites that keep their own list of results."""
	print("RESULT " + json.dumps({
		"suite": suite,
		"total": len(names),
		"passed": len(names) - len(failures),
		"failed": len(failures),
		"failures": list(failures),
		"tests": list(names),
	}, ensure_ascii=False))
	sys.stdout.flush()
