# Relatório de testes da versão 1.7.0

* Pacote: `dist/NotasWorkflowNVDA-1.7.0.nvda-addon`
* SHA-256: `7fb47faaf7ddf2b4229e2406b9d5ee427e28b120f53fd3e9e1936bba868503f3`
* Ambiente: Windows 11, NVDA 2026.1.1 instalado, Python 3.11 e 3.13, wxPython 4.3.1, bandit, MSAA (comtypes)
* Mudanças: sem o campo Tags na janela da folha (Tab de Status direto para Conteúdo); tags fora da descrição das folhas, dos documentos exportados e da busca; as tags do arquivo continuam guardadas

## Resultado final

**694 testes · 694 aprovados · 0 falhas.** O pacote foi gerado por `python build.py --release`, que roda todas as suítes antes e recusa gerar o pacote se alguma falhar.

| Suíte | Testes | Aprovados | Falharam |
|---|---|---|---|
| Unidades (Python 3.11, NVDA 2024.1–2025.x) | 101 | 101 | 0 |
| Unidades (Python 3.13, NVDA 2026.x) | 101 | 101 | 0 |
| Interface | 182 | 182 | 0 |
| Acessibilidade (inglês, com MSAA) | 99 | 99 | 0 |
| Acessibilidade (português, com MSAA) | 99 | 99 | 0 |
| Tradução | 10 | 10 | 0 |
| Segurança (vulnerabilidades e privacidade) | 40 | 40 | 0 |
| NVDA instalado | 6 | 6 | 0 |
| Desempenho (100 mil folhas) | 33 | 33 | 0 |
| Pacote | 2 | 2 | 0 |
| Manual de uso (HTML) | 21 | 21 | 0 |

Casos novos ou mudados:

* FUN-31 (sem tags): a janela da folha não tem o campo Tags.
* ACE-03: ordem de Tab da janela da folha Título, Local, Status, Conteúdo, Formatação, Situação do salvamento, Salvar e fechar. ACE-18: a folha é lida pelo MSAA sem as tags.
* FUN-10 e FUN-22: a busca não acha uma folha só pela tag. FUN-27: o documento exportado não traz as tags. FUN-03: o salvamento automático conferido com uma mudança de título.

## Execuções completas (`reports/execucoes.json`)

| Nº | Testes | Aprovados | Falhas | Corrigidos | Observação |
|---|---|---|---|---|---|
| 21 | 694 | 694 | 0 | 0 | Sem o campo Tags |
| 22 | 694 | 694 | 0 | 0 | `build.py --release` (portão da versão) |

As falhas vistas durante o desenvolvimento estão em [PROBLEMAS-1.7.0.md](PROBLEMAS-1.7.0.md) (nenhuma).

## Roteiro manual

MAN-38 de [TESTES-MANUAIS.md](../docs/TESTES-MANUAIS.md) (janela da folha sem Tags com o NVDA de verdade): pendente.
