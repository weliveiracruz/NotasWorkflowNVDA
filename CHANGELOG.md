# Histórico de versões

## 1.1.0

* **Novo nome: Notas Workflow NVDA.** O nome interno passa a `NotasWorkflowNVDA`: pacote `NotasWorkflowNVDA-<versão>.nvda-addon`, categoria "Notas Workflow NVDA" nas Configurações e em Definir comandos, item "Notas Workflow NVDA…" no menu Ferramentas, pasta das folhas `%APPDATA%\nvda\NotasWorkflowNVDA` e arquivo `NotasWorkflowNVDA-data.json`.
* **Migração automática:** no primeiro início, as folhas da pasta padrão antiga (`%APPDATA%\nvda\NotasWorkflow`) e as configurações da seção `[NotasWorkflow]` são **copiadas** para o novo nome; numa pasta das folhas escolhida por você, o arquivo `NotasWorkflow-data.json` é copiado para o nome novo. Nada do complemento antigo é movido ou apagado. O NVDA avisa quantas folhas foram trazidas.
* Como o NVDA trata o novo nome como outro complemento, **desinstale o NotasWorkflow 1.0.0** depois de conferir as folhas, para os atalhos NVDA+Alt+N, F e B não ficarem repetidos.
* O formato do arquivo continua o mesmo (`notas-workflow`), compatível com a aplicação web e com a versão anterior.

## 1.0.0

Primeira versão, com o mesmo fluxo da aplicação web Notas Workflow:

* **Quadro** em árvore de raias (A fazer, Em andamento, Bloqueada, Concluída) ou em tabela (Título, Status, Caderno, Tags, Atualizada em).
* **Mostrar**: todas as folhas, folhas soltas, folhas recentes, um caderno ou uma pasta.
* **Nova folha** (NVDA+Alt+F) com título, caderno e status; **janela da folha** com título, caderno, status, tags e conteúdo.
* **Conteúdo** com marcação leve convertida para o HTML do editor web (TipTap): negrito, itálico, tachado, código, títulos, listas, citação e divisor, pelo menu Formatação… ou Ctrl+B e Ctrl+I.
* **Salvamento automático** (2 s, configurável), Ctrl+S, e fechar a janela ou encerrar o NVDA sempre salvam.
* **Mover entre raias** com Mover para… ou Alt+Shift+Setas; **mudar caderno**; **excluir** com confirmação.
* **Buscar** (NVDA+Alt+B) sem diferenciar acentos e maiúsculas, com trecho e relevância.
* **Cadernos e pastas**: criar, renomear, mover e excluir (sem apagar folhas).
* **Arquivo** JSON com gravação atômica e cópia de segurança; pasta configurável (pode ser do OneDrive ou do Google Drive); **importar e exportar** no formato da aplicação web.
* Sem internet: nenhuma folha sai do computador.
* **Manual de uso detalhado em Word** (`docs/Manual-NotasWorkflowNVDA.docx`), gerado a cada build e conferido pelos testes.
