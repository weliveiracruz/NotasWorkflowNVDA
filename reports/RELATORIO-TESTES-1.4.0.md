# Relatório de testes da versão 1.4.0

* Pacote: `dist/NotasWorkflowNVDA-1.4.0.nvda-addon`
* SHA-256: `a4ad3a4df1655fe276a40b2572d83005e1c27b64a28aea1781bd96e365ea9e75`
* Ambiente: Windows 11, NVDA 2026.1.1 instalado, Python 3.11 e 3.13, wxPython 4.3.1, bandit, MSAA (comtypes), Microsoft Word (conferência do .docx)
* Mudanças: botão Exportar… na janela principal; a folha selecionada, um caderno ou uma pasta como documento do Word (.docx), Markdown (.md) ou página HTML (.html), num arquivo só ou num arquivo para cada folha (novo módulo `exporter.py`)

## Resultado final

**632 testes · 632 aprovados · 0 falhas.** O pacote foi gerado por `python build.py --release`, que roda todas as suítes antes e recusa gerar o pacote se alguma falhar.

| Suíte | Testes | Aprovados | Falharam |
|---|---|---|---|
| Unidades (Python 3.11, NVDA 2024.1–2025.x) | 97 | 97 | 0 |
| Unidades (Python 3.13, NVDA 2026.x) | 97 | 97 | 0 |
| Interface | 154 | 154 | 0 |
| Acessibilidade (inglês, com MSAA) | 88 | 88 | 0 |
| Acessibilidade (português, com MSAA) | 88 | 88 | 0 |
| Tradução | 10 | 10 | 0 |
| Segurança (vulnerabilidades e privacidade) | 40 | 40 | 0 |
| NVDA instalado | 6 | 6 | 0 |
| Desempenho (100 mil folhas) | 31 | 31 | 0 |
| Pacote | 2 | 2 | 0 |
| Manual de uso em Word | 19 | 19 | 0 |

Casos novos:

* FUN-27 (exportar): 11 testes de unidade (estrutura e níveis de título, Markdown, HTML, .docx válido e igual para as mesmas folhas, listas numeradas, caracteres inválidos, nomes de arquivo, nunca sobrescrever) e 20 verificações de interface (menu, escolhas que já vêm marcadas, os três formatos, um arquivo por folha, cancelar, caderno vazio, falha de gravação).
* SEG-01, SEG-06 e SEG-08: HTML exportado só com as tags dos formatos; títulos perigosos viram nomes de arquivo limpos dentro da pasta escolhida.
* PERF-14: exportar a maior pasta das 100 mil folhas. A janela responde em 0,05 s; a gravação em segundo plano leva 2,7 s (um arquivo Word) e 8,2 s (um Markdown por folha).

Conferência no Word: o .docx de exemplo abre sem aviso de reparo; os títulos usam os estilos Título 1 a 4, as listas com marcadores e numeradas (inclusive começando no 3) são listas do Word, e a citação, o bloco de código e o divisor têm estilos próprios.

## Execuções completas (`reports/execucoes.json`)

| Nº | Testes | Aprovados | Falhas | Corrigidos | Observação |
|---|---|---|---|---|---|
| 14 | 632 | 632 | 0 | 0 | Exportar como documento (Word, Markdown, HTML) |
| 15 | 632 | 632 | 0 | 0 | `build.py --release` (portão da versão) |

As falhas vistas antes da execução nº 14 apareceram rodando suítes isoladas durante o desenvolvimento e estão em [PROBLEMAS-1.4.0.md](PROBLEMAS-1.4.0.md).

## Problemas

* Do complemento: **3** (P-01 a P-03), todos corrigidos.
* Dos testes: **4** (T-01 a T-04), todos corrigidos.

## Roteiro manual

MAN-29 a MAN-31 de [TESTES-MANUAIS.md](../docs/TESTES-MANUAIS.md) (exportar com o NVDA de verdade e ler o documento no Word, no navegador e no Explorador de Arquivos): feitos pela pessoa responsável em 2026-10-21, sem problemas relatados.
