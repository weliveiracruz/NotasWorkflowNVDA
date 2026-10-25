# Relatório de testes da versão 1.5.0

* Pacote: `dist/NotasWorkflowNVDA-1.5.0.nvda-addon`
* SHA-256: `d8076a8a92453b89e3f0b3f5d7c9cb932323ff271500a1aea0eb0ee5ded05dc0`
* Ambiente: Windows 11, NVDA 2026.1.1 instalado, Python 3.11 e 3.13, wxPython 4.3.1, bandit, MSAA (comtypes)
* Mudanças: campo Local em árvore de pastas e cadernos (Nova folha, janela da folha e Mover para; novo módulo `locationTree.py` e janela `prompts.PlaceDialog`); botão Manual de uso… e comando sem atalho que abrem o manual na janela de leitura do NVDA; o manual em Word deixou de ser gerado (o manual agora é `addon/doc/pt_BR/manual.html`, dentro do pacote)

## Resultado final

**673 testes · 673 aprovados · 0 falhas.** O pacote foi gerado por `python build.py --release`, que roda todas as suítes antes e recusa gerar o pacote se alguma falhar.

| Suíte | Testes | Aprovados | Falharam |
|---|---|---|---|
| Unidades (Python 3.11, NVDA 2024.1–2025.x) | 97 | 97 | 0 |
| Unidades (Python 3.13, NVDA 2026.x) | 97 | 97 | 0 |
| Interface | 171 | 171 | 0 |
| Acessibilidade (inglês, com MSAA) | 99 | 99 | 0 |
| Acessibilidade (português, com MSAA) | 99 | 99 | 0 |
| Tradução | 10 | 10 | 0 |
| Segurança (vulnerabilidades e privacidade) | 40 | 40 | 0 |
| NVDA instalado | 6 | 6 | 0 |
| Desempenho (100 mil folhas) | 31 | 31 | 0 |
| Pacote | 2 | 2 | 0 |
| Manual de uso (HTML) | 21 | 21 | 0 |

Casos novos:

* FUN-28 (campo Local em árvore): 13 verificações de interface (estrutura da árvore, pastas fechadas, só a pasta do local aberta, pasta como local, Enter cria, janela da folha salva a mudança, Mover para começa no local atual, Enter move, Cancelar mantém).
* FUN-29 (manual de uso): botão e comando abrem o manual inteiro em HTML na janela de leitura do NVDA; manual ausente é falado.
* ACE-03, ACE-08, ACE-14 e ACE-18: ordem de tabulação com Manual de uso e com a janela Mover para; nome "Local" da árvore também pelo MSAA; pasta lida com o número de cadernos e "recolhido"; título da janela Mover para com a folha.
* DOC-01 a DOC-06 refeitos para o HTML: arquivo bem formado e igual ao do pacote, sem manual em Word, atualizado pela fonte e pela versão, um h1, capítulos em h2, seções em h3, tabelas com cabeçalho, sumário com links, sem script nem imagem.
* FUN-16: `ui.browseableMessage` com `isHtml` existe no NVDA instalado.

## Execuções completas (`reports/execucoes.json`)

| Nº | Testes | Aprovados | Falhas | Corrigidos | Observação |
|---|---|---|---|---|---|
| 16 | 667 | 665 | 2 | 0 | Campo Local em árvore (desempenho afetado pelo Defender, veja T-03) |
| 17 | 673 | 673 | 0 | 2 | `build.py --release` (portão da versão), com o manual em HTML |

As falhas vistas durante o desenvolvimento estão em [PROBLEMAS-1.5.0.md](PROBLEMAS-1.5.0.md).

## Problemas

* Do complemento: **1** (P-01), corrigido.
* Dos testes: **3** (T-01 a T-03); T-01 e T-02 corrigidos; T-03 foi do ambiente (Defender) e não se repetiu na execução nº 17.

## Roteiro manual

MAN-32 a MAN-35 de [TESTES-MANUAIS.md](../docs/TESTES-MANUAIS.md) (árvore Local e Manual de uso com o NVDA de verdade): pendentes.
