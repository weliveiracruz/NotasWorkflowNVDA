# -*- coding: UTF-8 -*-
"""Mede o tempo de cada operação da interface com uma massa grande de folhas.

Uso:  python tests/medir_desempenho.py [arquivo da massa]
      padrão: dados-teste/massa-100000-folhas.json (gere com tests/gerar_massa.py)

Roda numa pasta temporária: as folhas reais nunca são tocadas."""

import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from _guiapp import (  # noqa: E402
	NotasWorkflowNVDA, closeWindow, fakeModal, gui, mainDialog, newPlugin, noteDialog, organizeDialog, pump, searchDialog, store, wx,
)
import _helpers  # noqa: E402

RESULTS = []
WRITES = []


PLUGIN = []


def medir(nome, func):
	if PLUGIN:
		# Steady state: the previous change already written (as when the person reads the
		# result before the next command). The time of the writes is measured apart.
		start = time.perf_counter()
		PLUGIN[0].store.flush()
		WRITES.append(time.perf_counter() - start)
	start = time.perf_counter()
	result = func()
	elapsed = time.perf_counter() - start
	RESULTS.append((nome, elapsed))
	print("%-58s %7.2f s" % (nome, elapsed), flush=True)
	return result


def main():
	source = sys.argv[1] if len(sys.argv) > 1 else os.path.join(_helpers.ROOT, "dados-teste", "massa-100000-folhas.json")
	folder = _helpers.tempFolder()
	shutil.copy(source, os.path.join(folder, store.FILE_NAME))
	import config

	config.conf.spec[NotasWorkflowNVDA.CONFIG_SECTION] = NotasWorkflowNVDA.CONFIG_SPEC
	config.conf[NotasWorkflowNVDA.CONFIG_SECTION]["dataFolder"] = folder
	plugin = medir("Iniciar o NVDA (o complemento fica pronto)", NotasWorkflowNVDA.GlobalPlugin)
	medir("Ler as folhas (em segundo plano)", plugin.ensureLoaded)
	PLUGIN.append(plugin)
	print("   folhas: %d" % len(plugin.store.notes))
	dlg = medir("Abrir a janela enquanto a busca é preparada", plugin.openWindow)
	medir("Preparar a busca (em segundo plano, termina em)", lambda: plugin.indexReady.wait(120))
	closeWindow()
	dlg = medir("Abrir a janela (NVDA+Alt+N)", plugin.openWindow)
	note = plugin.store.getNote(dlg.selectedNoteId())
	medir("Atualizar o status (Alt+Shift+Seta)", lambda: dlg.moveBy(1))
	medir("Trocar o filtro para um caderno", lambda: dlg.setFilter(("notebook", plugin.store.notebooks[0]["id"])))
	medir("Voltar para Todas as folhas", lambda: dlg.setFilter(("all", None)))

	def editar(d):
		d.contentEdit.SetValue(d.contentEdit.GetValue() + "\nmais uma linha")
		d.finish()

	with fakeModal(noteDialog.NoteDialog, editar):
		medir("Abrir, editar e fechar uma folha (salva e atualiza)", lambda: dlg.openNote(note["id"]))
	medir("Gravar uma alteração (só o arquivo)", plugin.store.save)
	sd = searchDialog.SearchDialog(gui.mainFrame, plugin)
	sd.queryEdit.ChangeValue("genérico222")
	medir("Primeira busca (prepara o texto das folhas)", lambda: sd.runSearch(announce=False))
	sd.queryEdit.ChangeValue("nps cartoes")
	medir("Busca seguinte", lambda: sd.runSearch(announce=False))
	sd.close()

	def organizar():
		od = organizeDialog.OrganizeDialog(gui.mainFrame, plugin)
		od.Show()
		return od

	od = medir("Abrir Cadernos e pastas", organizar)
	medir("Abrir um caderno na árvore", lambda: od.expandKey(("notebook", plugin.store.notebooks[0]["id"])))
	medir("Atualizar a árvore de Cadernos e pastas", lambda: od.refresh())
	od.close()
	medir("Fechar a janela principal", closeWindow)
	print("%-58s %7.2f s" % ("Maior espera por uma gravação em segundo plano", max(WRITES or [0])))
	plugin.terminate()
	shutil.rmtree(folder, ignore_errors=True)


if __name__ == "__main__":
	main()
	os._exit(0)
