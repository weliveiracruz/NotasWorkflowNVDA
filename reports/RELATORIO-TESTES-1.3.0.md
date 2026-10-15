# Relatório de testes da versão 1.3.0

* Pacote: `dist/NotasWorkflowNVDA-1.3.0.nvda-addon`
* SHA-256: `3717d2aab565776f2c58b8304d0a37ba92ad8b24c618c2eb8082d11ed03f6b8d`
* Ambiente: Windows 11, NVDA 2026.1.1 instalado, Python 3.11 e 3.13, wxPython 4.3.1, bandit, MSAA (comtypes)
* Mudanças: as raias começam fechadas e ficam como a pessoa as deixou; depois de mudar o status ou o local de uma folha na janela dela, ao fechar a janela o foco vai para a próxima folha da mesma raia

## Resultado final

**582 testes · 582 aprovados · 0 falhas.** O pacote foi gerado por `python build.py --release`, que roda todas as suítes antes e recusa gerar o pacote se alguma falhar.

| Suíte | Testes | Aprovados | Falharam |
|---|---|---|---|
| Unidades (Python 3.11, NVDA 2024.1–2025.x) | 86 | 86 | 0 |
| Unidades (Python 3.13, NVDA 2026.x) | 86 | 86 | 0 |
| Interface | 134 | 134 | 0 |
| Acessibilidade (inglês, com MSAA) | 88 | 88 | 0 |
| Acessibilidade (português, com MSAA) | 88 | 88 | 0 |
| Tradução | 10 | 10 | 0 |
| Segurança (vulnerabilidades e privacidade) | 37 | 37 | 0 |
| NVDA instalado | 6 | 6 | 0 |
| Desempenho (100 mil folhas) | 26 | 26 | 0 |
| Pacote | 2 | 2 | 0 |
| Manual de uso em Word | 19 | 19 | 0 |

Casos novos: FUN-25 (raias fechadas: 5 verificações), FUN-26 (pilha da raia: 5 verificações) e PERF-05 (raias fechadas com 100 mil folhas).

## Execuções completas (`reports/execucoes.json`)

| Nº | Testes | Aprovados | Falhas | Corrigidos | Observação |
|---|---|---|---|---|---|
| 11 | 565 | 563 | 2 | 0 | `build.py --release`: testes que supunham uma folha já selecionada ao abrir (T-02, T-03) |
| 12 | 582 | 580 | 2 | 0 | `build.py --release`: digitação de fora caindo nas janelas dos testes (T-04) |
| 13 | 582 | 582 | 0 | 2 | `build.py --release` (portão da versão) |

## Problemas

* Do complemento: nenhum.
* Dos testes: **4** (T-01 a T-04), todos corrigidos; ver [PROBLEMAS-1.3.0.md](PROBLEMAS-1.3.0.md). O T-04 explica também a instabilidade vista na 1.2.0.

## Pendente: roteiro manual

MAN-01 a MAN-28 de [TESTES-MANUAIS.md](../docs/TESTES-MANUAIS.md), em especial MAN-27 (raias fechadas) e MAN-28 (pilha da raia).
