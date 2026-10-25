# Histórico de versões

## 1.7.0

* **Sem o campo Tags**: a janela da folha ficou com Título, Local, Status e Conteúdo; o Tab vai de **Status** direto para **Conteúdo**.
* As tags também saíram da descrição das folhas (lista de folhas e Cadernos e pastas), das linhas abaixo do título nos documentos exportados e da busca.
* Nada é apagado: as tags que uma folha já tinha continuam no arquivo de folhas, sem mudança, e vão junto na exportação e na importação de folhas.

## 1.6.0

* **Ordem das folhas na raia**: na lista de folhas, **Ctrl+Shift+Seta para cima** sobe a folha selecionada uma posição dentro da raia e **Ctrl+Shift+Seta para baixo** a desce. A seleção acompanha a folha e o NVDA diz a nova posição ("Posição 2 de 5"); nas pontas, "Já está no topo da raia" ou "Já está no fim da raia".
* A ordem é a da lista de folhas, a mesma em todos os filtros; a data de alteração da folha não muda. Com um caderno ou uma pasta mostrada, a folha passa a vizinha que aparece. Em Folhas recentes, que seguem a última alteração, o NVDA avisa que a ordem não pode ser mudada.

## 1.5.0

* **O campo Local virou uma árvore de pastas e cadernos**, que se abre como as raias: Folha solta, cada pasta (fechada, com o número de cadernos) com os cadernos dela dentro, e os cadernos sem pasta. Seta para a direita abre a pasta; Seta para a esquerda fecha.
* A folha pode ir para um caderno ou **direto para uma pasta**, sem caderno: basta escolher a própria pasta.
* A árvore está na janela **Nova folha**, na **janela da folha** e em **Mover para…**, sempre começando no local atual, com só a pasta dele aberta.
* Enter na árvore cria a folha (Nova folha) ou move a folha (Mover para). A janela Mover para diz no título qual folha está sendo movida.
* **Manual de uso… (Alt+N)** na janela principal: o manual detalhado vem dentro do complemento e abre na janela de leitura do NVDA, com títulos, tabelas e sumário navegáveis. Também há um comando sem atalho em Definir comandos. O manual em Word deixou de ser gerado.

## 1.4.0

* **Exportar… (Alt+E)** na janela principal: um menu com **Folha selecionada…**, **Caderno…** e **Pasta…**. O caderno ou a pasta mostrada (ou o da folha selecionada) já vem escolhido.
* Três formatos: **documento do Word (.docx)**, **Markdown (.md)** e **página HTML (.html)**, gerados pelo próprio complemento, sem precisar de nenhum programa instalado.
* Caderno e pasta: **um arquivo com todas as folhas** (o caderno ou a pasta como título 1, cada caderno da pasta como título 2 e cada folha como título abaixo, na ordem das raias) ou **um arquivo para cada folha**, numa pasta nova com o nome do caderno ou da pasta e uma subpasta para cada caderno.
* Cada folha exportada traz o título, o status, as tags, as datas e o conteúdo com a formatação (negrito, itálico, tachado, código, títulos, listas, citações e divisores). Os títulos são navegáveis pelo leitor de telas no Word e no navegador, e o documento tem idioma e título.
* Nada é sobrescrito sem perguntar: o arquivo único pergunta antes de substituir, e a exportação de um arquivo por folha cria uma pasta nova ("Trabalho (2)" se "Trabalho" já existe). A gravação acontece em segundo plano, e o NVDA fala quantas folhas foram exportadas e onde.

## 1.3.0

* **As raias começam fechadas**: a lista mostra só as raias com o número de folhas; Seta para a direita abre uma raia. A raia de uma folha selecionada pelo complemento abre sozinha, e as raias ficam como você as deixou.
* **Pilha da raia**: ao mudar o status ou o local de uma folha na janela dela e fechar a janela, o foco vai para a próxima folha da mesma raia (a anterior, se era a última; a raia, se era a única), e não para a folha movida.

## 1.2.0

* **Criar…** no lugar de Nova folha: um menu para criar uma folha, um caderno ou uma pasta, na janela principal e em Cadernos e pastas.
* **Atualizar o status da tarefa…** no lugar do antigo Mover para (status).
* **Mover para…** agora move a folha para um caderno, **direto para uma pasta** ou a deixa solta; o campo Caderno da folha virou **Local**.
* **Enter abre a folha**; o botão Abrir saiu.
* Só a visualização em raias: a tabela e a caixa Visualização saíram.
* **Cadernos e pastas** lista as folhas de cada caderno e pasta, e Enter abre a folha; Renomear muda o título da folha, Mover para e Excluir também valem para folhas.
* **Desempenho com 100 mil folhas:** o NVDA inicia na hora (as folhas são lidas em segundo plano); a gravação acontece em segundo plano, juntando mudanças seguidas e terminando antes de o NVDA fechar; a busca prepara o texto das folhas uma vez (de 7 s para frações de segundo); mudar o status e editar uma folha só atualizam a parte da lista que mudou; listas de 200 em 200 com "Mostrar mais folhas"; reabrir a janela é instantâneo. Arquivos de até 200 MB.
* Correção: a seleção da lista podia pular para outra folha quando a lista recebia o foco.
* Os textos de uso não citam mais outra plataforma.

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
