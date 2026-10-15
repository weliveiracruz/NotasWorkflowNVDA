# Problemas encontrados na versão 1.3.0

Versão de dois ajustes de comportamento pedidos: as raias começam fechadas, e, depois de mudar o status ou o local de uma folha na janela dela, o foco vai para a próxima folha da mesma raia ao fechar a janela.

## Problemas do complemento (P)

Nenhum.

## Problemas dos testes (T)

| ID | Teste | Causa | Correção |
|---|---|---|---|
| T-01 | test_gui: FUN-25 raias ficam como a pessoa deixou | O teste abria a raia Concluída, que estava vazia; uma raia sem folhas não abre | O teste abre a raia Bloqueada, que tem folha |
| T-02 | test_performance: PERF-06 (execução nº 11) | O teste usava a folha selecionada ao abrir a janela; com as raias fechadas, a seleção começa na primeira raia, sem folha | O teste escolhe uma folha antes de medir; novo PERF-05 confere raias fechadas e a raia da folha escolhida aberta |
| T-04 | test_gui: FUN-23 e FUN-24 instáveis (execução nº 12; também T-08 da 1.2.0) | As janelas dos testes são reais e às vezes pegam o primeiro plano; quando alguém digita no computador ao mesmo tempo, as teclas caem na árvore do teste e a busca por digitação do Windows seleciona outra folha ("E" de Entregue, "D" de Direto na pasta). Confirmado mandando um "e" de fora: a seleção mudou | Nos testes, toda entrada real de teclado e mouse é descartada antes de chegar aos controles (`_TestApp.FilterEvent`); as teclas dos testes vão direto para os tratadores. No complemento nada muda: a busca por digitação é o comportamento esperado de uma árvore |
| T-03 | test_gui: FUN-24 (execução nº 11) | O teste selecionava "Mostrar mais" dentro de uma raia fechada | Seleciona com `selectItem`, como o complemento, que abre a raia |
