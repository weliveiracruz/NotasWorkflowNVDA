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
