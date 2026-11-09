# Relatório de testes da versão 1.11.0

* Pacote: `dist/NotasWorkflowNVDA-1.11.0.nvda-addon`
* SHA-256: `c7edc173ad2bb03fa0a14c55ac4c2a0b26c6b15dcb7cb0796f42b709f61a95b3`
* Ambiente: Windows 11, NVDA 2026.1.1 instalado, Python 3.11 e 3.13, wxPython 4.3.1, bandit, MSAA (comtypes)
* Mudanças: botão Nova pasta… (Alt+V) na janela Novo caderno, com a pasta criada já escolhida na lista Pasta (a pasta selecionada lida no campo Mostrar foi experimentada e desfeita a pedido; veja as execuções)

## Resultado final

**796 testes · 796 aprovados · 0 falhas.** O pacote foi gerado por `python build.py --release`, que roda todas as suítes antes e recusa gerar o pacote se alguma falhar.

| Suíte | Testes | Aprovados | Falharam |
|---|---|---|---|
| Unidades (Python 3.11, NVDA 2024.1–2025.x) | 115 | 115 | 0 |
| Unidades (Python 3.13, NVDA 2026.x) | 115 | 115 | 0 |
| Interface | 232 | 232 | 0 |
| Acessibilidade (inglês, com MSAA) | 107 | 107 | 0 |
| Acessibilidade (português, com MSAA) | 107 | 107 | 0 |
| Tradução | 10 | 10 | 0 |
| Segurança (vulnerabilidades e privacidade) | 45 | 45 | 0 |
| NVDA instalado | 6 | 6 | 0 |
| Desempenho (100 mil folhas) | 36 | 36 | 0 |
| Pacote | 2 | 2 | 0 |
| Manual de uso (HTML) | 21 | 21 | 0 |

Casos novos e alterados:

* FUN-38 (Nova pasta no Novo caderno): 5 verificações de interface: o botão; nome cancelado não cria e devolve o foco; a pasta entra na lista Pasta escolhida, com o foco e o anúncio; o caderno vai para a pasta nova com o nome digitado; Mostrar recebe a pasta com o caderno dentro.
* ACE-03: a ordem de tabulação do Novo caderno é Nome, Pasta, Nova pasta, Criar, Cancelar; letras de atalho únicas em inglês e em português.

## Execuções completas (`reports/execucoes.json`)

| Nº | Testes | Aprovados | Falhas | Corrigidos | Observação |
|---|---|---|---|---|---|
| 29 | 802 | 802 | 0 | 0 | 1.11.0: Nova pasta no Novo caderno e pasta selecionada em Mostrar |
| 30 | 802 | 802 | 0 | 0 | `build.py --release` com a pasta selecionada (FUN-37); pacote descartado |
| 31 | 796 | 796 | 0 | 0 | Sem o "selecionada" em Mostrar, desfeito a pedido depois do teste com o NVDA (FUN-37 retirado) |
| 32 | 796 | 796 | 0 | 0 | `build.py --release` (portão da versão) |

## Problemas

* Do complemento: nenhum.
* Dos testes: nenhum (não há `PROBLEMAS-1.11.0.md`).

## Roteiro manual

MAN-50 de [TESTES-MANUAIS.md](../docs/TESTES-MANUAIS.md) (Nova pasta no Novo caderno, com o NVDA de verdade): pendentes.
