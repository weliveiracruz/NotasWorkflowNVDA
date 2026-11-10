# Relatório de testes da versão 1.12.0

* Pacote: `dist/NotasWorkflowNVDA-1.12.0.nvda-addon`
* SHA-256: `54d120cc6018a0fa82d057502c7c1c49214c5c757cddf4472ed46e08c6bbe379`
* Ambiente: Windows 11, NVDA 2026.1.1 instalado, Python 3.11 e 3.13, wxPython 4.3.1, bandit, MSAA (comtypes)
* Mudanças: excluir um caderno exclui as folhas dele; excluir uma pasta exclui os cadernos dela, as folhas desses cadernos e as folhas direto na pasta (antes as folhas ficavam soltas), com a contagem na pergunta; a janela principal não tem mais os botões Atualizar o status da tarefa…, Mover para… e Excluir (Alt+Shift+Setas, Delete e a janela da folha continuam; Mover para… continua em Cadernos e pastas)

## Resultado final

**800 testes · 800 aprovados · 0 falhas.** O pacote foi gerado por `python build.py --release`, que roda todas as suítes antes e recusa gerar o pacote se alguma falhar.

| Suíte | Testes | Aprovados | Falharam |
|---|---|---|---|
| Unidades (Python 3.11, NVDA 2024.1–2025.x) | 117 | 117 | 0 |
| Unidades (Python 3.13, NVDA 2026.x) | 117 | 117 | 0 |
| Interface | 234 | 234 | 0 |
| Acessibilidade (inglês, com MSAA) | 106 | 106 | 0 |
| Acessibilidade (português, com MSAA) | 106 | 106 | 0 |
| Tradução | 10 | 10 | 0 |
| Segurança (vulnerabilidades e privacidade) | 45 | 45 | 0 |
| NVDA instalado | 6 | 6 | 0 |
| Desempenho (100 mil folhas) | 36 | 36 | 0 |
| Pacote | 2 | 2 | 0 |
| Manual de uso (HTML) | 21 | 21 | 0 |

Casos novos e alterados:

* FUN-40 (exclusão em cascata): 7 verificações de interface (pergunta com a contagem, Não mantém, Sim exclui caderno e folhas, a árvore se atualiza, pasta pela tecla Delete com cadernos e folhas, cadernos de outras pastas ficam, pasta vazia) e 4 testes de unidade (caderno, pasta, vazios, gravação no arquivo); os 2 testes de unidade antigos que esperavam as folhas soltas foram trocados.
* FUN-39 (janela principal sem botões da folha): 1 verificação de interface; FUN-07 passou a usar só Alt+Shift+Setas (saiu o menu do botão); FUN-08 passou a usar o Mover para do complemento, que fica em Cadernos e pastas; FUN-09 exclui com a tecla Delete.
* ACE-03/ACE-04: a ordem de tabulação da janela principal é Mostrar, Folhas, Criar, Buscar, Cadernos e pastas, Exportar, Manual de uso, Fechar, com e sem folhas (uma verificação a menos: a do foco depois do botão Mover para).
* SEG-09: excluir um caderno exclui só as folhas dele; as outras ficam.
* ACE-17: o texto do botão Atualizar o status da tarefa saiu da tradução; a verificação do arquivo compilado usa Cadernos e pastas.

## Execuções completas (`reports/execucoes.json`)

| Nº | Testes | Aprovados | Falhas | Corrigidos | Observação |
|---|---|---|---|---|---|
| 33 | 800 | 800 | 0 | 0 | 1.12.0: exclusão em cascata de caderno e pasta; sem botões de folha na janela principal |
| 34 | 800 | 800 | 0 | 0 | `build.py --release` (portão da versão) |

## Problemas

* Do complemento: **1**, corrigido nesta versão: excluir uma pasta ou um caderno deixava as folhas soltas, sem caderno e sem pasta, em vez de excluí-las (relatado pela pessoa responsável). O web (`lib/store.ts`) continua soltando as folhas; a diferença está registrada no SDD (RF-35).
* Dos testes: nenhum.

## Roteiro manual

MAN-51 a MAN-53 de [TESTES-MANUAIS.md](../docs/TESTES-MANUAIS.md) (janela principal sem os botões da folha e exclusão em cascata, com o NVDA de verdade): pendentes.
