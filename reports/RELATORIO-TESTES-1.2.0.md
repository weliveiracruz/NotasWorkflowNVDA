# Relatório de testes da versão 1.2.0

* Pacote: `dist/NotasWorkflowNVDA-1.2.0.nvda-addon`
* SHA-256: `c2ba9d36425e4aa59588709522bd34de47032b7755a8e3d5a9b7aff9b83e034e`
* Ambiente: Windows 11, NVDA 2026.1.1 instalado, Python 3.11 e 3.13, wxPython 4.3.1, bandit, MSAA (comtypes)
* Mudanças: Criar (folha, caderno e pasta), Atualizar o status da tarefa, Mover para (caderno ou pasta), Enter abre a folha, sem tabela e sem o botão Abrir, folhas em Cadernos e pastas, campo Local, desempenho com 100 mil folhas, textos de uso sem outra plataforma

## Resultado final

**570 testes · 570 aprovados · 0 falhas.** O pacote foi gerado por `python build.py --release`, que roda todas as suítes antes e recusa gerar o pacote se alguma falhar.

| Suíte | Testes | Aprovados | Falharam |
|---|---|---|---|
| Unidades (Python 3.11, NVDA 2024.1–2025.x) | 86 | 86 | 0 |
| Unidades (Python 3.13, NVDA 2026.x) | 86 | 86 | 0 |
| Interface | 123 | 123 | 0 |
| Acessibilidade (inglês, com MSAA) | 88 | 88 | 0 |
| Acessibilidade (português, com MSAA) | 88 | 88 | 0 |
| Tradução | 10 | 10 | 0 |
| Segurança (vulnerabilidades e privacidade) | 37 | 37 | 0 |
| NVDA instalado | 6 | 6 | 0 |
| Desempenho (100 mil folhas) — nova | 25 | 25 | 0 |
| Pacote | 2 | 2 | 0 |
| Manual de uso em Word | 19 | 19 | 0 |

## Desempenho com 100 mil folhas

Medianas de três execuções de `tests/medir_desempenho.py` (cada operação medida depois de a gravação anterior terminar):

| Operação | 1.1.0 | 1.2.0 |
|---|---|---|
| NVDA pronto ao iniciar | 3,5 s parado | 0 s (leitura em segundo plano: 3,5 s) |
| Abrir a janela | 0,3 s | 0,2 s; reabrir: 0 s |
| Atualizar o status | 1,2 s | 0,36 s |
| Abrir, editar e fechar uma folha | 3,8 s | 0,2 s |
| Gravar uma alteração | 0,6 s parado | 0 s (em segundo plano) |
| Primeira busca | 7,2 s (antes do índice: até 92 s) | 0,1 a 0,2 s |
| Busca seguinte | 0,26 s | 0,08 a 0,6 s |
| Abrir Cadernos e pastas | 0,7 s | 0,1 s |

## Execuções completas (`reports/execucoes.json`)

| Nº | Testes | Aprovados | Falhas | Corrigidos | Observação |
|---|---|---|---|---|---|
| 7 | 570 | 570 | 0 | 0 | 1.2.0 completa |
| 8 | 570 | 570 | 0 | 0 | `build.py --release` (portão da versão) |

Antes da primeira execução completa, cada suíte foi rodada isoladamente durante a construção; as falhas dessas rodadas estão em [PROBLEMAS-1.2.0.md](PROBLEMAS-1.2.0.md).

## Problemas

* Do complemento: **9** (P-01 a P-09), todos corrigidos, entre eles a seleção da árvore que podia pular para outra folha (P-08) e a gravação que travava a interface (P-05).
* Dos testes: **7** (T-01 a T-07), todos corrigidos.
* Do manual: **1** (D-01), corrigido.

## Pendente: roteiro manual

MAN-01 a MAN-25 de [TESTES-MANUAIS.md](../docs/TESTES-MANUAIS.md), em especial MAN-23 a MAN-25 (uso real com 100 mil folhas no NVDA falando).
