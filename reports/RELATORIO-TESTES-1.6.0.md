# Relatório de testes da versão 1.6.0

* Pacote: `dist/NotasWorkflowNVDA-1.6.0.nvda-addon`
* SHA-256: `a75ef786e8e94615adb7b0bbabf32cef6075ea32b3468b536c1fa0b091cf8a8a`
* Ambiente: Windows 11, NVDA 2026.1.1 instalado, Python 3.11 e 3.13, wxPython 4.3.1, bandit, MSAA (comtypes)
* Mudanças: Ctrl+Shift+Seta para cima e para baixo na lista de folhas sobem ou descem a folha uma posição dentro da raia (novo `Store.placeNoteBeside` e `NotesDialog.reorder`); só os dois itens da árvore trocam de texto; novas mensagens faladas da posição, das pontas da raia e de Folhas recentes

## Resultado final

**693 testes · 693 aprovados · 0 falhas.** O pacote foi gerado por `python build.py --release`, que roda todas as suítes antes e recusa gerar o pacote se alguma falhar.

| Suíte | Testes | Aprovados | Falharam |
|---|---|---|---|
| Unidades (Python 3.11, NVDA 2024.1–2025.x) | 101 | 101 | 0 |
| Unidades (Python 3.13, NVDA 2026.x) | 101 | 101 | 0 |
| Interface | 181 | 181 | 0 |
| Acessibilidade (inglês, com MSAA) | 99 | 99 | 0 |
| Acessibilidade (português, com MSAA) | 99 | 99 | 0 |
| Tradução | 10 | 10 | 0 |
| Segurança (vulnerabilidades e privacidade) | 40 | 40 | 0 |
| NVDA instalado | 6 | 6 | 0 |
| Desempenho (100 mil folhas) | 33 | 33 | 0 |
| Pacote | 2 | 2 | 0 |
| Manual de uso (HTML) | 21 | 21 | 0 |

Casos novos:

* FUN-30 (ordem na raia): 4 testes de unidade (antes ou depois da vizinha, só a ordem muda e `updatedAt` fica igual, já no lugar ou ela mesma não muda nada, folha desconhecida é erro, ordem gravada no arquivo) e 10 verificações de interface (subir e descer com a seleção acompanhando e "Posição n de total", topo e fim falados, ordem mantida ao refazer a árvore, vizinha mostrada num caderno, aviso em Folhas recentes, nada numa raia, fim de página passa a primeira folha ainda não mostrada).
* PERF-15: Ctrl+Shift+Seta com 100 mil folhas em 0,04 s (limite 1 s), com a folha continuando selecionada.

## Execuções completas (`reports/execucoes.json`)

| Nº | Testes | Aprovados | Falhas | Corrigidos | Observação |
|---|---|---|---|---|---|
| 19 | 693 | 692 | 1 | 0 | Ordem da folha na raia (DOC-06, veja T-01) |
| 20 | 693 | 693 | 0 | 1 | `build.py --release` (portão da versão) |

As falhas vistas durante o desenvolvimento estão em [PROBLEMAS-1.6.0.md](PROBLEMAS-1.6.0.md).

## Problemas

* Do complemento: nenhum.
* Dos testes: **1** (T-01), corrigido.

## Roteiro manual

MAN-36 e MAN-37 de [TESTES-MANUAIS.md](../docs/TESTES-MANUAIS.md) (ordem na raia com o NVDA de verdade): pendentes.
