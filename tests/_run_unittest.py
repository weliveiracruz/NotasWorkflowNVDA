# -*- coding: UTF-8 -*-
"""Runs the unit tests (test_pure.py) and prints a RESULT line for run_all.py."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from _results import emit  # noqa: E402


class _Collect(unittest.TextTestResult):
	def __init__(self, *a, **k):
		super().__init__(*a, **k)
		self.names = []

	def startTest(self, test):
		self.names.append(test.id().split(".", 1)[-1])
		super().startTest(test)


def main():
	suite = unittest.defaultTestLoader.discover(HERE, pattern="test_pure.py")
	runner = unittest.TextTestRunner(verbosity=1, resultclass=_Collect)
	result = runner.run(suite)
	failed = [t.id().split(".", 1)[-1] for t, _tb in result.failures + result.errors]
	label = "unit (python %d.%d)" % sys.version_info[:2]
	emit(label, result.names, failed)
	return 1 if failed else 0


if __name__ == "__main__":
	sys.exit(main())
