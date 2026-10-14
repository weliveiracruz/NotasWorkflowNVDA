# Roteiro de testes manuais do NotasWorkflowNVDA

O que os testes automáticos não alcançam: a fala real do NVDA, a sincronização entre computadores e a troca de arquivos com a aplicação web. Faça a cada nova versão, com o NVDA instalado.

Anote o resultado (OK ou o problema) em `reports/RELATORIO-TESTES-<versão>.md`.

| ID | Passos | Esperado |
|---|---|---|
| MAN-01 | Instalar o `.nvda-addon` e reiniciar o NVDA | Instalação sem aviso de incompatibilidade |
| MAN-02 | NVDA+Alt+N | Janela "Notas Workflow NVDA"; NVDA lê "Folhas: Todas as folhas (0), árvore" e "A fazer, 0 folhas" |
| MAN-03 | Nova folha…, digitar título, Enter | NVDA fala "Folha criada em A fazer"; a janela da folha abre no Conteúdo |
| MAN-04 | Digitar no conteúdo e parar 2 segundos; Tab até a Situação do salvamento | "Salva às HH:MM" |
| MAN-05 | Selecionar uma palavra e Ctrl+B; Formatação… > Lista com marcadores | NVDA fala "Negrito" e "Lista com marcadores"; o texto mostra `**palavra**` e `- ` |
| MAN-06 | Esc na janela da folha | A janela fecha, o foco volta para a folha na árvore, nada se perde |
| MAN-07 | Na árvore, Alt+Shift+Seta para a direita três vezes e mais uma | "Movida para Em andamento", "Bloqueada", "Concluída", depois "Já está na última raia" |
| MAN-08 | Mover para… | Menu com as três outras raias; escolher uma move a folha |
| MAN-09 | Visualização: Tabela; Seta para baixo | NVDA lê título, status, caderno, tags e data de cada linha |
| MAN-10 | Cadernos e pastas…: nova pasta, novo caderno dentro dela, F2, Delete | Cada ação falada; Delete pergunta antes; as folhas ficam soltas |
| MAN-11 | Mostrar: Caderno: <nome> | Só as folhas do caderno; rótulo com o número |
| MAN-12 | NVDA+Alt+B, digitar uma palavra sem acento de uma folha com acento | "Encontrado: 1 folha"; Tab vai aos resultados; Enter abre |
| MAN-13 | Delete numa folha, responder Não; depois Sim | Não mantém; Sim exclui e fala "Folha excluída: …" |
| MAN-14 | Exportar folhas…, abrir o arquivo na aplicação web (colar no `localStorage`) | As folhas aparecem nas raias certas, com o conteúdo formatado |
| MAN-15 | Na aplicação web, rodar o comando do manual no Console, salvar o `.json` e Importar folhas… | NVDA fala "Importado: …"; as folhas aparecem com caderno e raia |
| MAN-16 | Configurações > Notas Workflow NVDA > Procurar…, escolher uma pasta do OneDrive, OK | "Folhas salvas na nova pasta"; o arquivo aparece no OneDrive |
| MAN-17 | Em outro computador com a mesma pasta, criar uma folha; voltar e NVDA+Alt+N | A folha nova aparece |
| MAN-18 | Fechar o NVDA no meio da digitação (antes dos 2 s) e reabrir | Nada se perde: o complemento salva a folha aberta ao encerrar; o arquivo abre normalmente |
| MAN-19 | Definir comandos > Notas Workflow NVDA > atribuir um atalho ao resumo das raias e usá-lo | "A fazer 2, Em andamento 1, Bloqueada 0, Concluída 3" |
| MAN-20 | Desinstalar o complemento | As folhas continuam em `%APPDATA%\nvda\NotasWorkflowNVDA` |
| MAN-21 | Com o NotasWorkflow 1.0.0 instalado e com folhas, instalar o Notas Workflow NVDA e reiniciar | NVDA fala "Folhas da versão anterior trazidas para o Notas Workflow NVDA: N folhas…"; NVDA+Alt+N mostra as mesmas folhas; `%APPDATA%\nvda\NotasWorkflow` continua intacta |
| MAN-22 | Desinstalar o NotasWorkflow 1.0.0 e reiniciar | NVDA+Alt+N, F e B abrem só o Notas Workflow NVDA; o aviso de migração não se repete |
