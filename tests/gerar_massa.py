# -*- coding: UTF-8 -*-
"""Gera um arquivo de importação com muitas folhas para testar desempenho (busca,
abertura da janela, importação). Resultado sempre igual (semente fixa).

Uso:  python tests/gerar_massa.py [quantidade] [arquivo]
      padrão: 100000 folhas em dados-teste/massa-<quantidade>-folhas.json

Cada folha é de um projeto de pesquisa: likert1, CES2, binário3, pms4, nps5,
genérico6... (o número é global, então cada nome aparece uma vez), com objetivo,
escala, público, responsável, métricas e tags. As folhas ficam em cadernos e
pastas; algumas ficam soltas. O conteúdo usa a mesma conversão do complemento
(markup.textToHtml), então é exatamente o HTML que ele grava."""

import datetime
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

import _helpers  # noqa: E402

core = _helpers.loadCore()
markup, model = core.markup, core.model

TYPES = [
	("likert", "Likert", "escala de concordância de 5 pontos"),
	("CES", "CES", "esforço do cliente (Customer Effort Score), de 1 a 7"),
	("binário", "Binário", "pergunta de sim ou não"),
	("pms", "PMS", "satisfação pós-atendimento (PMS)"),
	("nps", "NPS", "probabilidade de recomendação, de 0 a 10"),
	("genérico", "Genérico", "questionário aberto, sem escala fixa"),
]
AREAS = ["Cartões", "Investimentos", "Conta corrente", "Crédito imobiliário", "Seguros", "Atendimento digital", "Agências",
	"Câmbio", "Consórcio", "Previdência", "Empresas", "Varejo", "Aplicativo", "Internet banking", "Central de relacionamento"]
CANAIS = ["e-mail", "SMS", "aplicativo", "WhatsApp", "URA", "site", "totem na agência", "pop-up no internet banking"]
PUBLICOS = ["clientes pessoa física", "clientes pessoa jurídica", "novos clientes", "clientes de alta renda", "aposentados", "universitários", "lojistas"]
NOMES = ["Ana Souza", "Bruno Lima", "Carla Mendes", "Diego Rocha", "Elisa Prado", "Felipe Nunes", "Gabriela Costa", "Henrique Alves",
	"Isabela Duarte", "João Pedro", "Karina Freitas", "Lucas Martins", "Mariana Teles", "Nicolas Barros", "Olívia Ramos", "Paulo Vieira"]
OBJETIVOS = ["medir a satisfação depois do atendimento", "entender o motivo de cancelamentos", "avaliar a nova jornada de cadastro",
	"comparar a experiência entre canais", "identificar atritos no pagamento", "acompanhar a recomendação trimestral",
	"validar o novo fluxo de contestação", "medir o esforço para abrir conta", "priorizar melhorias do aplicativo"]
FOLDERS = ["Projetos 2025", "Projetos 2026", "Varejo", "Atacado", "Canais digitais", "Agências e atendimento",
	"Pesquisas contínuas", "Pilotos", "Arquivo morto", "Diretoria", "Squad de dados", "Experiência do cliente"]
NOTEBOOKS_PER_FOLDER = 6
LOOSE_NOTEBOOKS = 8
#: Parte das folhas sem caderno (folhas soltas), como no uso real.
LOOSE_SHARE = 0.05


def iso(dt):
	return model.nowIso(dt)


def gerar(count):
	"""Os dados de uma massa de count folhas (sempre os mesmos para o mesmo count)."""
	rnd = random.Random(20261013)
	start = datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)

	folders = []
	for i, name in enumerate(FOLDERS):
		folders.append({"id": "pasta-%02d" % (i + 1), "name": name, "color": model.FOLDER_COLORS[i % len(model.FOLDER_COLORS)], "createdAt": iso(start)})
	notebooks = []
	for f in folders:
		for j in range(NOTEBOOKS_PER_FOLDER):
			area = AREAS[(len(notebooks)) % len(AREAS)]
			notebooks.append({"id": "caderno-%03d" % (len(notebooks) + 1), "name": "%s - %s" % (area, f["name"]), "color": model.NOTEBOOK_COLORS[len(notebooks) % len(model.NOTEBOOK_COLORS)], "folderId": f["id"], "createdAt": iso(start)})
	for j in range(LOOSE_NOTEBOOKS):
		notebooks.append({"id": "caderno-%03d" % (len(notebooks) + 1), "name": "Avulso %d - %s" % (j + 1, AREAS[j]), "color": model.NOTEBOOK_COLORS[j % len(model.NOTEBOOK_COLORS)], "folderId": None, "createdAt": iso(start)})

	notes = []
	for n in range(1, count + 1):
		prefix, label, scale = TYPES[(n - 1) % len(TYPES)]
		project = "%s%d" % (prefix, n)
		area = rnd.choice(AREAS)
		canal = rnd.choice(CANAIS)
		publico = rnd.choice(PUBLICOS)
		dono = rnd.choice(NOMES)
		objetivo = rnd.choice(OBJETIVOS)
		respondentes = rnd.randint(50, 25000)
		taxa = rnd.randint(3, 48)
		nota = round(rnd.uniform(1, 10), 1)
		created = start + datetime.timedelta(minutes=rnd.randint(0, 650 * 24 * 60))
		updated = created + datetime.timedelta(minutes=rnd.randint(0, 60 * 24 * 60))
		text = "\n".join([
			"## Projeto %s" % project,
			"Pesquisa **%s** de %s para %s." % (label, area, publico),
			"Objetivo: %s." % objetivo,
			"- Escala: %s" % scale,
			"- Canal: %s" % canal,
			"- Respondentes: %d (taxa de resposta %d%%)" % (respondentes, taxa),
			"- Resultado atual: %s" % nota,
			"> Responsável: %s" % dono,
		])
		notebookId = None if rnd.random() < LOOSE_SHARE else rnd.choice(notebooks)["id"]
		notes.append({
			"id": "folha-%06d" % n,
			"title": "%s - %s %s" % (project, label, area),
			"content": markup.textToHtml(text),
			"tags": [prefix, area.lower(), canal],
			"laneId": rnd.choice(model.LANE_IDS),
			"notebookId": notebookId,
			"folderId": None,
			"createdAt": iso(created),
			"updatedAt": iso(updated),
		})

	return {"format": "notas-workflow", "version": 1, "folders": folders, "notebooks": notebooks, "notes": notes}


def gravar(data, target):
	os.makedirs(os.path.dirname(target), exist_ok=True)
	with open(target, "w", encoding="utf-8", newline="\n") as f:
		json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
	return os.path.getsize(target)


def main():
	count = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
	target = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "dados-teste", "massa-%d-folhas.json" % count)
	data = gerar(count)
	size = gravar(data, target)
	print("%s: %d folhas, %d cadernos, %d pastas, %.1f MB" % (target, len(data["notes"]), len(data["notebooks"]), len(data["folders"]), size / 1024 / 1024))
	return target


if __name__ == "__main__":
	main()
