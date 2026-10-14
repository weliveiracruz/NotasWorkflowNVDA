# Relatório de testes da versão 1.1.0

* Pacote: `dist/NotasWorkflowNVDA-1.1.0.nvda-addon`
* SHA-256: `4b9a3c464e1e65d4dae313e859757f978fde373cf9f4c495da83f5cb2f023f68`
* Ambiente: Windows 11, NVDA 2026.1.1 instalado (com o NotasWorkflow 1.0.0 instalado), Python 3.11 e 3.13, wxPython 4.3.1, bandit, MSAA (comtypes)
* Mudança: novo nome **Notas Workflow NVDA** (nome interno `NotasWorkflowNVDA`) e migração, só por cópia, das folhas e configurações do NotasWorkflow 1.0.0

## Resultado final

**502 testes · 502 aprovados · 0 falhas.** O pacote foi gerado por `python build.py --release`, que roda todas as suítes antes e recusa gerar o pacote se alguma falhar.

| Suíte | Testes | Aprovados | Falharam |
|---|---|---|---|
| Unidades (Python 3.11, NVDA 2024.1–2025.x) | 76 | 76 | 0 |
| Unidades (Python 3.13, NVDA 2026.x) | 76 | 76 | 0 |
| Interface | 99 | 99 | 0 |
| Acessibilidade (inglês, com MSAA) | 89 | 89 | 0 |
| Acessibilidade (português, com MSAA) | 89 | 89 | 0 |
| Tradução | 10 | 10 | 0 |
| Segurança (vulnerabilidades e privacidade) | 37 | 37 | 0 |
| NVDA instalado | 6 | 6 | 0 |
| Pacote | 2 | 2 | 0 |
| Manual de uso em Word | 18 | 18 | 0 |

Casos novos: FUN-20 (4 de unidade e 6 de interface: cópia do arquivo antigo, nada do antigo alterado, cópia uma só vez, configurações e cópia de segurança trazidas, aviso falado) e SEG-11 (a migração só copia).

## Execuções completas (`reports/execucoes.json`)

| Nº | Testes | Aprovados | Falhas | Corrigidos | Observação |
|---|---|---|---|---|---|
| 5 | 502 | 502 | 0 | 0 | Novo nome e migração |
| 6 | 502 | 502 | 0 | 0 | `build.py --release` (portão da versão) |

## Problemas

Nenhum problema do complemento, dos testes ou do manual nesta versão (ver [PROBLEMAS-1.1.0.md](PROBLEMAS-1.1.0.md)).

## Observação sobre a acessibilidade

O teste de conflito de atalhos (ACE-09) desconsidera o NotasWorkflow 1.0.0 instalado nesta máquina, porque ele é a versão anterior do mesmo complemento. Enquanto os dois estiverem instalados, NVDA+Alt+N, F e B ficam repetidos: o manual e o aviso falado da migração pedem para desinstalar o antigo.

## Pendente: roteiro manual

MAN-01 a MAN-22 de [TESTES-MANUAIS.md](../docs/TESTES-MANUAIS.md), em especial MAN-21 e MAN-22 (migração real a partir do NotasWorkflow 1.0.0 instalado).
