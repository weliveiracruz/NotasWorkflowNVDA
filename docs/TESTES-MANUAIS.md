# Roteiro de testes manuais do NotasWorkflowNVDA

O que os testes automáticos não alcançam: a fala real do NVDA, a sincronização entre computadores e o uso com muitas folhas no NVDA de verdade. Faça a cada nova versão, com o NVDA instalado.

Anote o resultado (OK ou o problema) em `reports/RELATORIO-TESTES-<versão>.md`.

| ID | Passos | Esperado |
|---|---|---|
| MAN-01 | Instalar o `.nvda-addon` e reiniciar o NVDA | Instalação sem aviso de incompatibilidade |
| MAN-02 | NVDA+Alt+N | Janela "Notas Workflow NVDA"; NVDA lê "Folhas: Todas as folhas (0), árvore" e "A fazer, 0 folhas" |
| MAN-03 | Criar… (Alt+C) > Folha…, digitar título, Enter | NVDA fala "Folha criada em A fazer"; a janela da folha abre no Conteúdo |
| MAN-04 | Digitar no conteúdo e parar 2 segundos; Tab até a Situação do salvamento | "Salva às HH:MM" |
| MAN-05 | Selecionar uma palavra e Ctrl+B; Formatação… > Lista com marcadores | NVDA fala "Negrito" e "Lista com marcadores"; o texto mostra `**palavra**` e `- ` |
| MAN-06 | Esc na janela da folha | A janela fecha, o foco volta para a folha na árvore, nada se perde |
| MAN-07 | Na árvore, Alt+Shift+Seta para a direita três vezes e mais uma | "Status atualizado para Em andamento", "Bloqueada", "Concluída", depois "Já está na última raia" |
| MAN-08 | Atualizar o status da tarefa… (Alt+A) | Menu com os três outros status; escolher um muda o status e o NVDA fala o novo |
| MAN-09 | Mover para… (Alt+M) numa folha; escolher uma pasta, depois um caderno, depois Folha solta | NVDA fala "Agora em: …"; a lista começa no lugar atual; a folha aparece no lugar escolhido em Cadernos e pastas |
| MAN-10 | Cadernos e pastas…: Criar… > Pasta…, Criar… > Caderno… dentro dela, abrir o caderno, Enter numa folha, F2, Delete | Cada ação falada; Enter abre a folha; Delete pergunta antes; excluir caderno deixa as folhas soltas |
| MAN-11 | Mostrar: Caderno: <nome> | Só as folhas do caderno; rótulo com o número |
| MAN-12 | NVDA+Alt+B, digitar uma palavra sem acento de uma folha com acento | "Encontrado: 1 folha"; Tab vai aos resultados; Enter abre |
| MAN-13 | Delete numa folha, responder Não; depois Sim | Não mantém; Sim exclui e fala "Folha excluída: …" |
| MAN-14 | Exportar folhas… para um arquivo; em outra pasta das folhas (vazia), Importar folhas… com esse arquivo | NVDA fala "Exportado: N folhas" e depois "Importado: N folhas…"; as folhas aparecem com o mesmo status, caderno e pasta |
| MAN-15 | Importar de novo o mesmo arquivo | Nada é duplicado: "Importado: 0 folhas…" |
| MAN-16 | Configurações > Notas Workflow NVDA > Procurar…, escolher uma pasta do OneDrive, OK | "Folhas salvas na nova pasta"; o arquivo aparece no OneDrive |
| MAN-17 | Em outro computador com a mesma pasta, criar uma folha; voltar e NVDA+Alt+N | A folha nova aparece |
| MAN-18 | Fechar o NVDA no meio da digitação (antes dos 2 s) e reabrir | Nada se perde: o complemento salva a folha aberta ao encerrar; o arquivo abre normalmente |
| MAN-19 | Definir comandos > Notas Workflow NVDA > atribuir um atalho ao resumo das raias e usá-lo | "A fazer 2, Em andamento 1, Bloqueada 0, Concluída 3" |
| MAN-20 | Desinstalar o complemento | As folhas continuam em `%APPDATA%\nvda\NotasWorkflowNVDA` |
| MAN-21 | Com o NotasWorkflow 1.0.0 instalado e com folhas, instalar o Notas Workflow NVDA e reiniciar | NVDA fala "Folhas da versão anterior trazidas para o Notas Workflow NVDA: N folhas…"; NVDA+Alt+N mostra as mesmas folhas; `%APPDATA%\nvda\NotasWorkflow` continua intacta |
| MAN-22 | Desinstalar o NotasWorkflow 1.0.0 e reiniciar | NVDA+Alt+N, F e B abrem só o Notas Workflow NVDA; o aviso de migração não se repete |
| MAN-23 | Importar a massa de 100 mil folhas (`python tests/gerar_massa.py`) numa pasta vazia, reiniciar o NVDA, NVDA+Alt+N logo em seguida | O NVDA inicia na hora; se a janela for pedida antes de terminar a leitura, fala "Carregando as folhas…" e abre em seguida |
| MAN-24 | Com 100 mil folhas: Alt+Shift+Setas, Enter numa folha e Esc, NVDA+Alt+B com uma palavra comum | Cada resposta em menos de um segundo; o NVDA não para de falar |
| MAN-25 | Numa raia com mais de 200 folhas, ir até o fim e Enter em "Mostrar mais 200 folhas" | As próximas folhas aparecem e o foco vai para a primeira delas |
| MAN-26 | Na lista, descer com as setas até uma folha, Tab até um botão e Shift+Tab de volta, Enter | Abre a folha que estava selecionada (a seleção não pula para outra folha) |
| MAN-27 | NVDA+Alt+N com folhas em várias raias | NVDA lê a primeira raia como "recolhido"; Seta para a direita abre e Seta para baixo lê as folhas; ao fechar e reabrir a janela, as raias continuam como você deixou |
| MAN-28 | Abrir a primeira folha de uma raia com três folhas, mudar o Status, Esc | O foco fica na segunda folha da raia (a seguinte na pilha), e não na folha movida |
| MAN-29 | Selecionar uma folha com formatação, Alt+E, Folha selecionada, Documento do Word, salvar na Área de Trabalho e abrir no Word | NVDA lê o menu e as listas; fala "Exportado: 1 folha, em …"; no Word, a tecla H do NVDA (modo de navegação) e o painel de navegação mostram o título da folha e os títulos do conteúdo; listas, negrito e citação lidos certo |
| MAN-30 | Alt+E, Caderno, escolher um caderno com várias folhas, Página HTML, Um arquivo com todas as folhas; abrir no navegador | Título 1 com o caderno, título 2 em cada folha (H navega), Status e Tags abaixo de cada título |
| MAN-32 | Com uma pasta com dois cadernos e um caderno sem pasta: Criar… > Folha…, Tab até Local, setas, Seta para a direita na pasta, Seta para baixo, Enter num caderno da pasta | NVDA lê "Local, árvore", "Pasta …, 2 cadernos, recolhido"; a direita abre e lê os cadernos; Enter cria a folha no caderno escolhido |
| MAN-33 | Abrir uma folha, Alt+O, escolher a própria pasta (sem caderno), Esc; abrir Cadernos e pastas | A folha aparece direto na pasta, fora dos cadernos |
| MAN-34 | Mover para… (Alt+M) numa folha de um caderno dentro de uma pasta | Janela "Mover … para" com o foco na árvore, no caderno atual, com só a pasta dele aberta; Enter num outro local move e fala "Agora em: …"; Esc não muda nada |
| MAN-35 | NVDA+Alt+N, Alt+N (Manual de uso…); H, 2, T e K no manual; Enter num link do sumário; Esc | A janela de leitura do NVDA abre com o manual em português; H e 2 passam pelos capítulos, T pelas tabelas (lidas com cabeçalho); o link do sumário leva ao capítulo; Esc fecha e o foco volta à janela principal |
| MAN-31 | Alt+E, Pasta, Markdown, Um arquivo para cada folha, escolher uma pasta; repetir a mesma exportação | Pasta nova com o nome da pasta, subpasta por caderno e um .md por folha; a segunda vez cria "Nome (2)" sem mexer na primeira |
| MAN-36 | Numa raia com três folhas, selecionar a terceira e pressionar Ctrl+Shift+Seta para cima duas vezes e mais uma | O NVDA lê a folha e "Posição 2 de 3", depois "Posição 1 de 3", depois "Já está no topo da raia"; Seta para baixo mostra a nova ordem |
| MAN-37 | Ctrl+Shift+Seta para baixo até o fim da raia; fechar e abrir a janela (NVDA+Alt+N); escolher Folhas recentes e pressionar Ctrl+Shift+Seta para baixo | "Já está no fim da raia"; a ordem continua a mesma depois de abrir de novo; em Folhas recentes o NVDA avisa que a ordem não pode ser mudada |
