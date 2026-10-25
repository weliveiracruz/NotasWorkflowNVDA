# -*- coding: UTF-8 -*-
"""Runs every NotasWorkflowNVDA test suite, counts the results and keeps the history.

Usage:  python tests/run_all.py [--note "text"]

Needs wxPython and bandit (pip install wxPython bandit comtypes). On Windows the
accessibility suite also reads the names through MSAA (comtypes). On Linux it
uses xvfb-run when there is no display.
Writes:
  reports/execucoes.json     - every execution (date, version, results per suite)
  reports/ULTIMA-EXECUCAO.md - summary of the last execution, in Portuguese
Exit code 0 only when every test passed."""

import datetime
import glob
import json
import os
import re
import shutil
import subprocess  # nosec B404 - test runner
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
REPORTS = os.path.join(ROOT, "reports")
HISTORY = os.path.join(REPORTS, "execucoes.json")


def version():
	with open(os.path.join(ROOT, "addon", "manifest.ini"), encoding="utf-8") as f:
		return re.search(r"^version\s*=\s*(\S+)", f.read(), re.M).group(1)


def _works(exe, code):
	try:
		return subprocess.run([exe, "-c", code], capture_output=True, timeout=60).returncode == 0  # nosec B603
	except (OSError, subprocess.TimeoutExpired):
		return False


def pythons():
	"""Every Python 3.11+ found (NVDA 2024.1-2025.x uses 3.11, NVDA 2026.x uses 3.13)."""
	candidates = [sys.executable]
	for v in ("3.11", "3.12", "3.13"):
		candidates.append(shutil.which("python" + v) or "")
		candidates += glob.glob(os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Python", "Python%s" % v.replace(".", ""), "python.exe"))
		candidates += glob.glob(os.path.join(os.environ.get("ProgramFiles", ""), "Python%s" % v.replace(".", ""), "python.exe"))
		# GitHub Actions (actions/setup-python) on Windows
		candidates += sorted(glob.glob(os.path.join(os.environ.get("RUNNER_TOOL_CACHE", ""), "Python", v + ".*", "x64", "python.exe")))
	# Any python on the PATH (Linux python3.x, setup-python, other installations)
	for folder in os.environ.get("PATH", "").split(os.pathsep):
		for name in ("python.exe", "python3", "python"):
			candidates.append(os.path.join(folder, name))
	found = {}
	for exe in candidates:
		if not exe or not os.path.exists(exe):
			continue
		try:
			out = subprocess.run([exe, "-c", "import sys;print('%d.%d' % sys.version_info[:2])"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60).stdout.strip()  # nosec B603
		except (OSError, subprocess.TimeoutExpired):
			continue
		if out in ("3.11", "3.12", "3.13") and out not in found:
			found[out] = exe
	return found


def runSuite(cmd, env=None, timeout=900):
	e = dict(os.environ)
	e.update(env or {})
	e["PYTHONIOENCODING"] = "utf-8"
	try:
		proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", env=e, timeout=timeout)  # nosec B603
		out = proc.stdout + proc.stderr
	except subprocess.TimeoutExpired as ex:
		out = (ex.stdout or "") if isinstance(ex.stdout, str) else ""
		out += "\nTIMEOUT"
	results = [json.loads(line[7:]) for line in out.splitlines() if line.startswith("RESULT ")]
	if not results:
		name = " ".join(os.path.basename(c) for c in cmd[-1:])
		return {"suite": name, "total": 1, "passed": 0, "failed": 1, "failures": ["suite did not finish: " + name], "tests": ["suite did not finish: " + name], "log": out[-3000:]}
	r = results[-1]
	r["log"] = out[-3000:] if r["failed"] else ""
	return r


def buildSuite(exe):
	tests = ["FUN-17 build.py validates the manifest and builds", "FUN-17 package has manifest, plugin, docs and translation"]
	failures = []
	proc = subprocess.run([exe, "-X", "utf8", "build.py"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")  # nosec B603
	pkg = os.path.join(ROOT, "dist", "NotasWorkflowNVDA-%s.nvda-addon" % version())
	if proc.returncode != 0 or not os.path.exists(pkg):
		failures += tests
	else:
		names = set(zipfile.ZipFile(pkg).namelist())
		needed = {"manifest.ini", "globalPlugins/NotasWorkflowNVDA/__init__.py", "globalPlugins/NotasWorkflowNVDA/store.py", "globalPlugins/NotasWorkflowNVDA/markup.py", "globalPlugins/NotasWorkflowNVDA/mainDialog.py", "doc/en/readme.html", "doc/pt_BR/readme.html", "locale/pt_BR/LC_MESSAGES/nvda.mo", "locale/pt_BR/manifest.ini"}
		if not needed <= names or any(n.endswith((".pyc", ".po")) or "__pycache__" in n for n in names):
			failures.append(tests[1])
	return {"suite": "package (build.py)", "total": 2, "passed": 2 - len(failures), "failed": len(failures), "failures": failures, "tests": tests, "log": proc.stdout[-1500:] + proc.stderr[-1500:] if failures else ""}


def main():
	note = ""
	if "--note" in sys.argv:
		note = sys.argv[sys.argv.index("--note") + 1]
	found = pythons()
	wxPython = next((exe for v, exe in sorted(found.items(), reverse=True) if _works(exe, "import wx")), None)
	xvfb = []
	if sys.platform != "win32" and not os.environ.get("DISPLAY") and shutil.which("xvfb-run"):
		xvfb = ["xvfb-run", "-a", "-s", "-screen 0 1400x1000x24"]
	suites = []
	for v, exe in sorted(found.items()):
		suites.append(runSuite([exe, "-X", "utf8", os.path.join("tests", "_run_unittest.py")]))
	if "3.11" not in found:
		suites.append({"suite": "unit (python 3.11)", "total": 1, "passed": 0, "failed": 1, "failures": ["Python 3.11 not found (NVDA 2024.1-2025.x)"], "tests": ["Python 3.11"], "log": ""})
	if wxPython:
		for script, env in (
			("test_gui.py", {}),
			("test_accessibility.py", {"NOTASWORKFLOWNVDA_LANG": "en"}),
			("test_accessibility.py", {"NOTASWORKFLOWNVDA_LANG": "pt_BR"}),
			("test_translation.py", {}),
			("test_security.py", {}),
			("test_nvda_runtime.py", {}),
			("test_performance.py", {}),
		):
			suites.append(runSuite(xvfb + [wxPython, "-X", "utf8", "-u", os.path.join("tests", script)], env=env))
	else:
		suites.append({"suite": "wxPython", "total": 1, "passed": 0, "failed": 1, "failures": ["wxPython not found: pip install wxPython"], "tests": ["wxPython"], "log": ""})
	suites.append(buildSuite(wxPython or sys.executable))
	# After the build, which regenerates the HTML manual (addon/doc/pt_BR/manual.html) from docs/manual/MANUAL.md.
	suites.append(runSuite([wxPython or sys.executable, "-X", "utf8", "-u", os.path.join("tests", "test_manual.py")]))

	os.makedirs(REPORTS, exist_ok=True)
	try:
		with open(HISTORY, encoding="utf-8") as f:
			runs = json.load(f)
	except (OSError, ValueError):
		runs = []
	previous = runs[-1] if runs else None
	prevFailed = set()
	if previous:
		for s in previous["suites"]:
			prevFailed.update("%s :: %s" % (s["suite"], t) for t in s["failures"])
	nowFailed = set()
	nowAll = set()
	for s in suites:
		nowFailed.update("%s :: %s" % (s["suite"], t) for t in s["failures"])
		nowAll.update("%s :: %s" % (s["suite"], t) for t in s.get("tests", []))
	corrected = sorted(t for t in prevFailed if t in nowAll and t not in nowFailed) if previous and previous["version"] == version() else []

	total = sum(s["total"] for s in suites)
	passed = sum(s["passed"] for s in suites)
	failed = sum(s["failed"] for s in suites)
	run = {
		"number": len(runs) + 1,
		"date": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
		"version": version(),
		"note": note,
		"pythons": sorted(found),
		"total": total,
		"passed": passed,
		"failed": failed,
		"corrected": corrected,
		"suites": [{k: s[k] for k in ("suite", "total", "passed", "failed", "failures")} for s in suites],
	}
	runs.append(run)
	with open(HISTORY, "w", encoding="utf-8") as f:
		json.dump(runs, f, ensure_ascii=False, indent=1)

	sameVersion = [r for r in runs if r["version"] == run["version"]]
	lines = [
		"# Última execução dos testes",
		"",
		"* Execução nº %d (%d nesta versão) em %s" % (run["number"], len(sameVersion), run["date"]),
		"* Versão: %s" % run["version"],
		"* Python: %s" % ", ".join(run["pythons"]),
	]
	if note:
		lines.append("* Observação: %s" % note)
	lines += [
		"* **Testes: %d · Aprovados: %d · Falharam: %d · Corrigidos desde a execução anterior: %d**" % (total, passed, failed, len(corrected)),
		"",
		"| Suíte | Testes | Aprovados | Falharam |",
		"|---|---|---|---|",
	]
	for s in suites:
		lines.append("| %s | %d | %d | %d |" % (s["suite"], s["total"], s["passed"], s["failed"]))
	if failed:
		lines += ["", "## Falhas", ""]
		for s in suites:
			for t in s["failures"]:
				lines.append("* %s: %s" % (s["suite"], t))
	if corrected:
		lines += ["", "## Corrigidos desde a execução anterior", ""]
		lines += ["* %s" % t for t in corrected]
	with open(os.path.join(REPORTS, "ULTIMA-EXECUCAO.md"), "w", encoding="utf-8") as f:
		f.write("\n".join(lines) + "\n")

	print("\n".join(lines))
	for s in suites:
		if s.get("log"):
			print("\n--- %s (log) ---\n%s" % (s["suite"], s["log"]))
	if os.environ.get("GITHUB_ACTIONS"):
		# Failures as annotations (readable on the public run page) and the run summary.
		for s in suites:
			for t in s["failures"]:
				print("::error title=%s::%s" % (s["suite"].replace(":", " "), t.replace("\n", " ")[:900]))
			if s.get("log"):
				print("::warning title=log %s::%s" % (s["suite"].replace(":", " "), s["log"][-900:].replace("\r", "").replace("\n", " | ")))
		summary = os.environ.get("GITHUB_STEP_SUMMARY")
		if summary:
			with open(summary, "a", encoding="utf-8") as f:
				f.write("\n".join(lines) + "\n")
	return 1 if failed else 0


if __name__ == "__main__":
	sys.exit(main())
