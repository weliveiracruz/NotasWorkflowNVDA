# Relatório de testes da versão 1.0.0

* Pacote: `dist/NotasWorkflow-1.0.0.nvda-addon`
* SHA-256: `420a6143c278f219ae44065f7989eeaa05632ca7d3fd4f7db10e7cc183fe9701`
* Ambiente: Windows 11, NVDA 2026.1.1 instalado, Python 3.11 e 3.13, wxPython 4.3.1, bandit, MSAA (comtypes)

## Resultado final

**487 testes · 487 aprovados · 0 falhas.** O pacote foi gerado por `python build.py --release`, que roda todas as suítes antes e recusa gerar o pacote se alguma falhar.

| Suíte | Testes | Aprovados | Falharam |
|---|---|---|---|
| Unidades (Python 3.11, NVDA 2024.1–2025.x) | 72 | 72 | 0 |
| Unidades (Python 3.13, NVDA 2026.x) | 72 | 72 | 0 |
| Interface | 93 | 93 | 0 |
| Acessibilidade (inglês, com MSAA) | 89 | 89 | 0 |
| Acessibilidade (português, com MSAA) | 89 | 89 | 0 |
| Tradução | 10 | 10 | 0 |
| Segurança (vulnerabilidades e privacidade) | 36 | 36 | 0 |
| NVDA instalado | 6 | 6 | 0 |
| Pacote | 2 | 2 | 0 |
| Manual de uso em Word | 18 | 18 | 0 |

## Execuções completas (`reports/execucoes.json`)

| Nº | Testes | Aprovados | Falhas | Corrigidos | Observação |
|---|---|---|---|---|---|
| 1 | 469 | 469 | 0 | 0 | Primeira execução completa |
| 2 | 469 | 469 | 0 | 0 | `build.py --release` (portão da versão) |
| 3 | 487 | 487 | 0 | 0 | Manual de uso em Word e suíte `test_manual` |
| 4 | 487 | 487 | 0 | 0 | `build.py --release` (portão da versão) |

Antes da primeira execução completa, cada suíte foi rodada isoladamente durante a construção; as falhas dessas rodadas estão em [PROBLEMAS-1.0.0.md](PROBLEMAS-1.0.0.md).

## Problemas

* Do complemento: **6** (P-01 a P-06), todos corrigidos.
* Dos testes: **4** (T-01 a T-04), todos corrigidos.
* Do manual: **1** (D-01), corrigido.

## Manual de uso

`docs/Manual-NotasWorkflow.docx` (13 páginas, 19 capítulos) foi aberto no Microsoft Word instalado e exportado para PDF para conferência visual: capa, sumário com links, listas, tabelas com cabeçalho repetido e rodapé com página.

## Pendente: roteiro manual

Os casos MAN-01 a MAN-20 de [TESTES-MANUAIS.md](../docs/TESTES-MANUAIS.md) precisam do NVDA falando, de uma pasta sincronizada em dois computadores e da aplicação web aberta no navegador; não foram executados de forma automática.
