# Problemas encontrados na versão 1.4.0

Versão da exportação como documento: botão Exportar… na janela principal, com a folha selecionada, um caderno ou uma pasta em Word (.docx), Markdown (.md) ou HTML (.html), num arquivo só ou num arquivo para cada folha. O PDF ficou de fora por decisão da pessoa responsável.

## Problemas do complemento (P)

Encontrados conferindo os arquivos gerados e nas primeiras execuções das suítes, antes da execução completa nº 14.

| ID | Onde | Causa | Correção |
|---|---|---|---|
| P-01 | Títulos do conteúdo | Um título 1 do conteúdo ficava no mesmo nível do título da folha (o conteúdo descia um nível a menos) | Os títulos 1 e 2 do conteúdo ficam um nível abaixo do título da folha, e o título 3 dois níveis abaixo |
| P-02 | Markdown | Um trecho só de espaços entre dois formatos (por exemplo, entre itálico e tachado) saía com o espaço duplicado | Trechos só de espaços são copiados como estão |
| P-03 | Word (.docx) | O bandit acusou `xml.sax.saxutils` (B406, aviso baixo), usado só para escapar texto | Escape com `html.escape`, sem módulo `xml` |

## Problemas dos testes (T)

| ID | Teste | Causa | Correção |
|---|---|---|---|
| T-01 | test_pure: FUN-27 Markdown | O teste esperava que a linha "1. não é lista" do conteúdo saísse como parágrafo; na marcação do editor ela é uma lista numerada, e a exportação mostra o que o editor mostra | O escape do Markdown é conferido com linhas de detalhes (Status, Tags), que nunca são marcação |
| T-02 | test_security: SEG-06 HTML exportado | A expressão procurava `onerror="` no texto e achava o texto escapado de uma folha (não um atributo) | O teste confere a lista de tags e de atributos do HTML exportado |
| T-03 | test_security: SEG-01 e SEG-03 | Os nomes fixos de XML que todo .docx declara (`http://schemas.openxmlformats.org/…`) pareciam endereços web; `zipfile` e `languageHandler` não estavam na lista de módulos permitidos | Só esses nomes de XML são aceitos, e só em `exporter.py`; `zipfile` (biblioteca padrão) e `languageHandler` (NVDA) entram na lista |
| T-04 | test_accessibility: ACE-03 e ACE-04 | A ordem de tabulação esperada não tinha o botão novo | Exportar entra entre Cadernos e pastas e Fechar |
