# Problemas encontrados na versão 1.6.0

Versão da ordem das folhas na raia: Ctrl+Shift+Seta para cima e para baixo na lista de folhas sobem ou descem a folha uma posição dentro da raia (novo `Store.placeNoteBeside` e `NotesDialog.reorder`). A ordem é a da lista de folhas, como no aplicativo web, sem campo novo no arquivo.

## Problemas do complemento (P)

Nenhum.

## Problemas dos testes (T)

| ID | Teste | Causa | Correção |
|---|---|---|---|
| T-01 | test_manual: DOC-06 | O manual e o changelog dos dois manifestos diziam que a ordem era "a mesma no aplicativo web"; os textos para o usuário não citam outra plataforma | A menção foi tirada do manual, dos manifestos e do CHANGELOG |
