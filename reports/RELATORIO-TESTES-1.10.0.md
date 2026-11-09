# Relatório de testes da versão 1.10.0

* Pacote: `dist/NotasWorkflowNVDA-1.10.0.nvda-addon`
* SHA-256: `e72e666c449827b6cdac6f59749e79c8831e7278f40403fc64b20c142558783a`
* Ambiente: Windows 11, NVDA 2026.1.1 instalado, Python 3.11 e 3.13, wxPython 4.3.1, bandit, MSAA (comtypes)
* Mudanças: a janela Nova folha ganhou os botões Novo caderno… (Alt+C) e Nova pasta… (Alt+P), depois do campo Local; o caderno ou a pasta criada entra na árvore Local, já escolhida, com o foco nela (`LocationTree.rebuild`); o Novo caderno começa na pasta escolhida em Local; a janela principal (Mostrar) e Cadernos e pastas se atualizam mesmo quando a Nova folha é cancelada

## Resultado final

**791 testes · 791 aprovados · 0 falhas.** O pacote foi gerado por `python build.py --release`, que roda todas as suítes antes e recusa gerar o pacote se alguma falhar.

| Suíte | Testes | Aprovados | Falharam |
|---|---|---|---|
| Unidades (Python 3.11, NVDA 2024.1–2025.x) | 115 | 115 | 0 |
| Unidades (Python 3.13, NVDA 2026.x) | 115 | 115 | 0 |
| Interface | 227 | 227 | 0 |
| Acessibilidade (inglês, com MSAA) | 107 | 107 | 0 |
| Acessibilidade (português, com MSAA) | 107 | 107 | 0 |
| Tradução | 10 | 10 | 0 |
| Segurança (vulnerabilidades e privacidade) | 45 | 45 | 0 |
| NVDA instalado | 6 | 6 | 0 |
| Desempenho (100 mil folhas) | 36 | 36 | 0 |
| Pacote | 2 | 2 | 0 |
| Manual de uso (HTML) | 21 | 21 | 0 |

Casos novos e alterados:

* FUN-36 (Novo caderno e Nova pasta na Nova folha): 10 verificações de interface: os botões; Nova pasta cria, fala e deixa a pasta escolhida em Local com o foco; Novo caderno começa na pasta escolhida em Local (a pasta ou a pasta do caderno) e fica escolhido dentro dela; o título digitado continua e a folha vai para o caderno novo; Mostrar recebe a pasta e o caderno; nomes cancelados não criam nada; cancelar a Nova folha mantém a pasta criada.
* ACE-03: a ordem de tabulação da Nova folha é Título, Local, Novo caderno, Nova pasta, Status, Criar, Cancelar; as letras de atalho continuam únicas em inglês e em português (verificação de ACE-02).

## Execuções completas (`reports/execucoes.json`)

| Nº | Testes | Aprovados | Falhas | Corrigidos | Observação |
|---|---|---|---|---|---|
| 27 | 791 | 791 | 0 | 0 | 1.10.0: Novo caderno e Nova pasta na Nova folha |
| 28 | 791 | 791 | 0 | 0 | `build.py --release` (portão da versão) |

## Problemas

* Do complemento: nenhum.
* Dos testes: nenhum (não há `PROBLEMAS-1.10.0.md`).

## Roteiro manual

MAN-47 a MAN-49 de [TESTES-MANUAIS.md](../docs/TESTES-MANUAIS.md) (Novo caderno e Nova pasta na Nova folha com o NVDA de verdade): pendentes.
