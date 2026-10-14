# -*- coding: UTF-8 -*-
"""Translation tests (ACE-12, ACE-17 of docs/SDD-TESTES.md): every interface text
is translated to Brazilian Portuguese, with the same placeholders and Alt shortcuts.

Run:  python tests/test_translation.py"""

import gettext
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import _strings  # noqa: E402
import build  # noqa: E402
from _results import Recorder  # noqa: E402

R = Recorder("translation (test_translation)")
PO = os.path.join(ROOT, "addon", "locale", "pt_BR", "LC_MESSAGES", "nvda.po")


def placeholders(s):
	return sorted(re.findall(r"\{\w+\}", s))


def run():
	po = build.parsePo(PO)
	po.pop("", None)
	used = {m for _p, _l, m, _ok in _strings.translatable()}
	missing = sorted(used - set(po))
	R.check("ACE-17 every interface text is translated to pt_BR", not missing, missing[:5])
	empty = sorted(k for k, v in po.items() if not v.strip())
	R.check("ACE-17 no empty translation", not empty, empty[:5])
	obsolete = sorted(set(po) - used)
	R.check("ACE-17 no obsolete texts in the translation", not obsolete, obsolete[:5])
	wrong = [k for k, v in po.items() if placeholders(k) != placeholders(v)]
	R.check("ACE-17 same {placeholders} in the translation", not wrong, wrong[:5])
	amp = [k for k, v in po.items() if (re.search(r"&[^&\s]", k) is None) != (re.search(r"&[^&\s]", v) is None)]
	R.check("ACE-02 Alt shortcut kept in the translation", not amp, amp[:5])
	ellipsis = [k for k, v in po.items() if k.endswith("…") != v.endswith("…")]
	R.check("ACE-17 '…' (opens a dialog) kept in the translation", not ellipsis, ellipsis)
	lanes = [po[k] for k in ("To do", "In progress", "Blocked", "Done")]
	R.check("ACE-17 lane names are the ones of the web app (types/index.ts)", lanes == ["A fazer", "Em andamento", "Bloqueada", "Concluída"], lanes)

	tmp = tempfile.mkdtemp()
	os.makedirs(os.path.join(tmp, "pt_BR", "LC_MESSAGES"))
	mo = os.path.join(tmp, "pt_BR", "LC_MESSAGES", "nvda.mo")
	build.writeMo(build.parsePo(PO), mo)
	t = gettext.translation("nvda", localedir=tmp, languages=["pt_BR"])
	R.check("ACE-17 compiled translation loads with gettext", t.gettext("C&reate note") == "C&riar folha" and t.gettext("{count} notes").format(count=3) == "3 folhas")

	man = build.readManifest(os.path.join(ROOT, "addon", "locale", "pt_BR", "manifest.ini"))
	R.check("ACE-17 add-on summary, description and changelog in pt_BR", all(man.get(k) for k in ("summary", "description", "changelog")))
	with open(os.path.join(ROOT, "docs", "pt_BR", "readme.md"), encoding="utf-8") as f:
		doc = f.read()
	R.check("ACE-17 pt_BR documentation lists every shortcut", all(k in doc for k in ("NVDA+Alt+N", "NVDA+Alt+F", "NVDA+Alt+B", "Alt+Shift+Seta para a direita", "Ctrl+S")))


if __name__ == "__main__":
	try:
		run()
	except Exception:
		import traceback

		traceback.print_exc()
		R.check("suite finished without crashing", False, traceback.format_exc()[-500:])
	sys.exit(R.finish())
