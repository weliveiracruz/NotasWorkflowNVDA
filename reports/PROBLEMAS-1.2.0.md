# Problemas encontrados na versão 1.2.0

Versão das mudanças pedidas na interface (Criar, Atualizar o status da tarefa, Mover para, Enter abre, sem tabela, folhas em Cadernos e pastas) e do desempenho com muitas folhas. Medidas com a massa de 100 mil folhas de `tests/gerar_massa.py` (`tests/medir_desempenho.py` e a nova suíte `tests/test_performance.py`). Todos corrigidos; a versão só foi gerada com 0 falhas.

## Problemas do complemento (P)

| ID | Onde apareceu | Gravidade | Causa | Correção |
|---|---|---|---|---|
| P-01 | Medição com 10, 20 e 100 mil folhas (PEND-01 da 1.1.0) | Alta | Cada busca convertia o HTML de todas as folhas e tirava os acentos letra por letra: 3 s com 10 mil folhas, 23 s com 20 mil, de 34 a 92 s com 100 mil, com o NVDA sem responder | Índice da busca (`SearchIndex`) com o texto de cada folha preparado uma vez e refeito só quando a folha muda; texto por expressão regular; acentos tirados de uma vez (NFKD + regex); só os 100 melhores ordenados. Busca: 0,1 a 0,5 s |
| P-02 | PEND-02 da 1.1.0 | Alta | O limite de 20 MB valia também para o próprio arquivo de dados, mas a gravação não o respeitava: com cerca de 28 mil folhas o arquivo seria tratado como danificado ao reabrir o NVDA | Limite de 200 MB para dados e importação; arquivo compacto (64 MB para 100 mil folhas) |
| P-03 | Medição | Alta | Mudar o status ou fechar uma folha refazia a árvore inteira (até 25 mil itens por raia) e gravava o arquivo inteiro na hora: 1,2 s e 3,8 s com 100 mil folhas | A árvore refaz só as raias afetadas ou troca o texto de um item; páginas de 200 folhas por raia com "Mostrar mais"; gravação em segundo plano. Status: 0,3 s; edição: 0,2 s |
| P-04 | Medição | Média | O NVDA ficava 3,5 s parado ao iniciar, lendo e validando as folhas | Leitura numa linha de execução; os comandos esperam com "Carregando as folhas…" |
| P-05 | Medição depois da gravação em segundo plano | Alta | `json.dumps` do arquivo inteiro prende o Python por cerca de 1 s mesmo em outra linha de execução: a interface travava ao gravar | JSON codificado folha por folha, com pausas a cada 500 folhas, meio segundo depois da última mudança (várias mudanças viram uma gravação) |
| P-06 | Medição | Média | A preparação da busca em segundo plano disputava o Python com a interface: abrir a janela levou 9,7 s | Preparação em lotes de 300 folhas com pausas |
| P-07 | Medição | Baixa | Cadernos e pastas contava as folhas percorrendo a lista inteira uma vez por caderno | Contagem por lugar numa passada só (`placeCounts`) |
| P-08 | test_gui: FUN-23 (instável) | Média | O Windows guarda o "item com foco" da árvore separado do item selecionado; quando a árvore recebia o foco, a seleção podia voltar a uma folha antiga, e Enter abria a folha errada | `selectItem` seleciona e marca o item com foco juntos, nas duas janelas; o caractere do Enter não chega mais à busca por digitação da árvore |
| P-09 | test_gui/test_security: fim das suítes | Baixa | Ao destruir as janelas, a árvore ainda enviava eventos de seleção com os botões já destruídos (`RuntimeError`) | `updateButtons` não faz nada quando os controles já não existem |

## Problemas dos testes (T)

| ID | Teste | Causa | Correção |
|---|---|---|---|
| T-01 | test_pure: FUN-22 | O teste trocava um item da lista de folhas diretamente, sem passar pelo store, caso que o índice por id não acompanha (e que o complemento nunca faz) | Parte removida; a regra ficou documentada no store |
| T-02 | test_gui: FUN-10 recentes | Esperava a ordem antiga da tabela; a árvore agrupa as recentes por raia | Confere o conjunto e a mais recente |
| T-03 | test_gui: FUN-24 | Esperava páginas de 500 | Usa `PAGE_SIZE` |
| T-04 | test_gui: FUN-17 e FUN-20 | Liam o arquivo ou as folhas antes de a gravação e a leitura em segundo plano terminarem | `flush()` e `ensureLoaded()` antes de conferir |
| T-05 | test_security: SEG-02 | Trocava a pasta por um caminho impossível antes de a gravação anterior terminar; a gravação adiada criou uma pasta com o nome do arquivo | `flush()` antes de trocar a pasta |
| T-06 | test_security: SEG-09 | Procurava "store.deleteNote", que também aparece em "store.deleteNotebook" | Procura a chamada exata |
| T-07 | test_manual | Ainda procurava textos da tabela e da caixa Visualização | Listas atualizadas; novo DOC-06 |
| T-08 | test_gui no GitHub (release da tag v1.2.0) | Na máquina do GitHub a janela do teste nem sempre recebe o foco: o Enter simulado de FUN-24 foi para um botão, que abriu um menu real; sem ninguém para escolher, a suíte esperou até o tempo esgotar e nada foi publicado. Aqui, com o painel do navegador em primeiro plano, os testes de foco real também falharam | Nos testes, nenhum menu ou caixa real pode abrir sem resposta (registrado em RECORD["blocked"] e conferido por FUN-16); sem foco do teclado, a tecla vai direto para quem a trata. A tag v1.2.0 foi refeita no commit corrigido |

## Problemas do manual (D)

| ID | Teste | Causa | Correção |
|---|---|---|---|
| D-01 | Revisão | O manual descrevia a tabela, o botão Abrir, Mudar caderno e citava a plataforma web | Manual reescrito para a 1.2.0; DOC-06 confere que manual, readmes, manifestos e interface não citam outra plataforma |
