# Problemas encontrados na versão 1.5.0

Versão do campo Local em árvore: Folha solta, cada pasta (fechada, com os cadernos dela dentro) e os cadernos sem pasta, na janela Nova folha, na janela da folha e em Mover para (novo módulo `locationTree.py` e janela `prompts.PlaceDialog`). O manual de uso deixou de ser gerado em Word: vai em HTML dentro do pacote (`addon/doc/pt_BR/manual.html`) e abre pelo botão Manual de uso…, por decisão da pessoa responsável.

## Problemas do complemento (P)

Encontrados nas primeiras execuções das suítes isoladas, antes da execução completa.

| ID | Onde | Causa | Correção |
|---|---|---|---|
| P-01 | Mover para | A pergunta "Mover … para:" ficava como texto acima da árvore, sem letra de atalho, e o título da folha com `&` era lido diferente pelo MSAA | A árvore tem o rótulo "Local" (Alt+O) e o título da janela diz a folha: "Mover … para" |

## Problemas dos testes (T)

| ID | Teste | Causa | Correção |
|---|---|---|---|
| T-01 | test_gui: FUN-08 e FUN-12; test_accessibility: ACE-07 | Os testes trocavam `prompts.chooseItem`, que Mover para não usa mais | Os testes trocam `prompts.choosePlace`, com a nova assinatura (janela, título, folhas, local atual) |
| T-03 | test_performance: PERF-06, 07, 09, 10 e 14 | Com o Microsoft Defender (proteção em tempo real) usando toda a CPU para analisar os arquivos gravados pelas suítes, os tempos ficaram de 2 a 15 vezes maiores (exportar em Word: 21 s contra 2,7 s na 1.4.0), em execuções diferentes falhando casos diferentes; nenhum desses casos passa pelo código mudado | Rodar de novo com a máquina livre; as configurações do Defender não foram mudadas |
| T-02 | test_accessibility: ACE-04 em Sem pasta | A pasta criada para conferir a árvore Local continuava nas folhas e mudava a janela Cadernos e pastas conferida depois | O teste apaga o caderno e a pasta que criou |
