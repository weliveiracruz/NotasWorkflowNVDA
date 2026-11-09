# Relatório de testes da versão 1.9.0

* Pacote: `dist/NotasWorkflowNVDA-1.9.0.nvda-addon`
* SHA-256: `ec1cc4ef78056e12a384b2f90fcc32ccae11487c1996c67fade91bcd5b24dcd1`
* Ambiente: Windows 11, NVDA 2026.1.1 instalado, Python 3.11 e 3.13, wxPython 4.3.1, bandit, MSAA (comtypes)
* Mudanças: o campo Mostrar da janela principal virou uma árvore, organizada como o campo Local (Todas as folhas, Folhas soltas, Folhas recentes, cada pasta com os cadernos dela dentro, os cadernos sem pasta); as pastas começam fechadas e só abre a do caderno mostrado; Enter em Mostrar vai para a lista de folhas; a árvore só é refeita quando pastas, cadernos ou nomes mudam

## Resultado final

**781 testes · 781 aprovados · 0 falhas.** O pacote foi gerado por `python build.py --release`, que roda todas as suítes antes e recusa gerar o pacote se alguma falhar.

| Suíte | Testes | Aprovados | Falharam |
|---|---|---|---|
| Unidades (Python 3.11, NVDA 2024.1–2025.x) | 115 | 115 | 0 |
| Unidades (Python 3.13, NVDA 2026.x) | 115 | 115 | 0 |
| Interface | 217 | 217 | 0 |
| Acessibilidade (inglês, com MSAA) | 107 | 107 | 0 |
| Acessibilidade (português, com MSAA) | 107 | 107 | 0 |
| Tradução | 10 | 10 | 0 |
| Segurança (vulnerabilidades e privacidade) | 45 | 45 | 0 |
| NVDA instalado | 6 | 6 | 0 |
| Desempenho (100 mil folhas) | 36 | 36 | 0 |
| Pacote | 2 | 2 | 0 |
| Manual de uso (HTML) | 21 | 21 | 0 |

Casos novos e alterados:

* FUN-35 (Mostrar em árvore): 6 verificações de interface: é uma árvore com o filtro em uso selecionado; selecionar um item mostra as folhas dele; o caderno de uma pasta fica dentro dela; escolher esse caderno abre a pasta; a árvore não é refeita quando nada nela mudou; Enter vai para a lista de folhas.
* FUN-10: a ordem das opções passou a ser todas, soltas, recentes, cada pasta (com seus cadernos) e os cadernos sem pasta.
* ACE-03/ACE-04: a ordem de tabulação começa pela árvore Mostrar.
* PERF-07: trocar para um caderno e voltar para todas as folhas com 100 mil folhas continua abaixo de 2 s (cerca de 0,5 s).

## Execuções completas (`reports/execucoes.json`)

| Nº | Testes | Aprovados | Falhas | Corrigidos | Observação |
|---|---|---|---|---|---|
| 25 | 781 | 781 | 0 | 0 | 1.9.0: campo Mostrar em árvore (pastas com seus cadernos) |
| 26 | 781 | 781 | 0 | 0 | `build.py --release` (portão da versão) |

## Problemas

* Do complemento: nenhum.
* Dos testes: nenhum (não há `PROBLEMAS-1.9.0.md`).

## Roteiro manual

MAN-44 a MAN-46 de [TESTES-MANUAIS.md](../docs/TESTES-MANUAIS.md) (árvore Mostrar com o NVDA de verdade): pendentes.
