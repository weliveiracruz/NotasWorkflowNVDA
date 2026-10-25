# Relatório de testes da versão 1.8.0

* Pacote: `dist/NotasWorkflowNVDA-1.8.0.nvda-addon`
* SHA-256: `efe9ed999142aaa6c8087694c154956f8685d93326f8275cfcc36d283a65cb07`
* Ambiente: Windows 11, NVDA 2026.1.1 instalado, Python 3.11 e 3.13, wxPython 4.3.1, bandit, MSAA (comtypes); Word e PowerPoint instalados (usados só para conferir arquivos reais durante o desenvolvimento)
* Mudanças: Criar > Folha a partir de documento… e comando sem atalho; botão Inserir documento… (Alt+D) na janela da folha; novo módulo `importer.py` (Word .docx, PowerPoint .pptx, texto, HTML e e-mail .eml, lidos em segundo plano); linhas de tabela no conversor de HTML; janela Novo caderno com a escolha da pasta; o temporizador da janela da folha para quando ela é destruída

## Resultado final

**775 testes · 775 aprovados · 0 falhas.** O pacote foi gerado por `python build.py --release`, que roda todas as suítes antes e recusa gerar o pacote se alguma falhar.

| Suíte | Testes | Aprovados | Falharam |
|---|---|---|---|
| Unidades (Python 3.11, NVDA 2024.1–2025.x) | 115 | 115 | 0 |
| Unidades (Python 3.13, NVDA 2026.x) | 115 | 115 | 0 |
| Interface | 211 | 211 | 0 |
| Acessibilidade (inglês, com MSAA) | 107 | 107 | 0 |
| Acessibilidade (português, com MSAA) | 107 | 107 | 0 |
| Tradução | 10 | 10 | 0 |
| Segurança (vulnerabilidades e privacidade) | 45 | 45 | 0 |
| NVDA instalado | 6 | 6 | 0 |
| Desempenho (100 mil folhas) | 36 | 36 | 0 |
| Pacote | 2 | 2 | 0 |
| Manual de uso (HTML) | 21 | 21 | 0 |

Casos novos:

* FUN-32 (Novo caderno com pasta): 6 verificações de interface; ACE-01/02/03/08 da janela Novo caderno.
* FUN-33 (leitura de documentos): 14 testes de unidade com documentos gerados pelos testes (`tests/_documents.py`): Word, PowerPoint, e-mail, HTML em duas codificações, texto em quatro codificações, erros, corte em 1 MB e tabelas.
* FUN-34 (Folha a partir de documento e Inserir documento): 24 verificações de interface, incluindo a leitura em segundo plano, a janela fechada durante a leitura, a folha cheia e Cadernos e pastas.
* SEG-13: bomba zip, XML com DTD e entidade externa, página com scripts e atributos, texto do documento fora do log.
* PERF-16: Word de 300 páginas (6.000 parágrafos) lido em 0,23 s em segundo plano; a chamada volta na hora; o HTML da folha em 0,05 s.
* Conferência manual durante o desenvolvimento: um .docx, um .pptx e uma página .htm gerados pelo próprio Word e PowerPoint foram lidos com títulos, listas, tabela, slides e anotações certos.

## Execuções completas (`reports/execucoes.json`)

| Nº | Testes | Aprovados | Falhas | Corrigidos | Observação |
|---|---|---|---|---|---|
| 23 | 775 | 773 | 2 | 0 | Folha a partir de documento, Inserir documento e caderno com pasta (ACE-02 do menu Criar, veja T-02) |
| 24 | 775 | 775 | 0 | 2 | `build.py --release` (portão da versão) |

As falhas vistas durante o desenvolvimento estão em [PROBLEMAS-1.8.0.md](PROBLEMAS-1.8.0.md).

## Problemas

* Do complemento: **3** (P-01 a P-03), corrigidos.
* Dos testes: **3** (T-01 a T-03); T-02 e T-03 corrigidos; T-01 contornado (os testes de documentos rodam antes) e com a causa ainda em aberto, também presente na 1.7.0.

## Roteiro manual

MAN-39 a MAN-43 de [TESTES-MANUAIS.md](../docs/TESTES-MANUAIS.md) (Novo caderno com pasta, Folha a partir de documento com cada tipo e Inserir documento, com o NVDA de verdade): pendentes.
