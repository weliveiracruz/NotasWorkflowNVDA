# Notas Workflow NVDA

Complemento do NVDA para organizar folhas (anotações e tarefas) em raias de status (A fazer, Em andamento, Bloqueada, Concluída), agrupadas em cadernos e pastas, com tags, conteúdo com formatação, salvamento automático e busca. Tudo funciona pelo teclado, com respostas faladas, e continua rápido com dezenas de milhares de folhas.

## A janela principal

Pressione **NVDA+Alt+N** (ou menu do NVDA, Ferramentas, **Notas Workflow NVDA…**). A janela tem:

* **Mostrar**: todas as folhas, folhas soltas (sem caderno nem pasta), folhas recentes (as 10 alteradas por último), um caderno ou uma pasta.
* **Folhas**: as folhas numa árvore com um ramo por raia ("A fazer, 3 folhas"). As raias começam fechadas: Seta para a direita abre, Seta para a esquerda fecha. Enter abre a folha, Delete exclui (depois de confirmar), **Alt+Shift+Seta para a direita** e **Alt+Shift+Seta para a esquerda** mudam o status, **Ctrl+Shift+Seta para cima** e **Ctrl+Shift+Seta para baixo** sobem ou descem a folha dentro da raia. Cada raia mostra 200 folhas por vez; "Mostrar mais folhas" no fim mostra as próximas.
* **Criar…**: um menu para criar uma folha, um caderno ou uma pasta.
* **Atualizar o status da tarefa…**: um menu com os outros status.
* **Mover para…**: move a folha para um caderno, direto para uma pasta ou a deixa solta.
* **Local** (na Nova folha, na janela da folha e em Mover para) é uma árvore que se abre como as raias: cada pasta começa fechada, com os cadernos dela dentro; escolher a própria pasta guarda a folha direto nela.
* **Excluir**, **Buscar…**, **Cadernos e pastas…** e **Fechar** (Esc).
* **Exportar…**: exporta a folha selecionada, um caderno ou uma pasta como documento (veja abaixo).
* **Manual de uso…** (Alt+N): abre o manual de uso detalhado na janela de leitura do NVDA, com títulos, tabelas e sumário. Um comando sem atalho em Definir comandos também o abre.

## Folhas

**Criar… > Folha…** (ou NVDA+Alt+F de qualquer lugar) pede o título, o local (solta, uma pasta ou um caderno) e o status e depois abre a janela da folha. A janela da folha tem título, local, status, tags (separadas por vírgula) e o conteúdo. Se você mudar o status ou o local ali, ao fechar a janela o foco vai para a próxima folha da mesma raia, para tratar a raia uma folha depois da outra. Ela salva sozinha 2 segundos depois que você para de digitar; Ctrl+S salva na hora e fechar a janela (Esc ou Salvar e fechar) sempre salva. Nada se perde.

O conteúdo é texto com uma marcação leve:

| Digite | Para ter |
|---|---|
| `## Título` ou `### Título` | Título 2 ou 3 |
| `- item` | Lista com marcadores |
| `1. item` | Lista numerada |
| `> texto` | Citação |
| `---` | Divisor |
| `**texto**` | Negrito (Ctrl+B) |
| `*texto*` | Itálico (Ctrl+I) |
| `~~texto~~` | Tachado |
| `` `texto` `` | Código |

O botão **Formatação…** abre um menu com todos os formatos; ele vale para o texto selecionado ou para a linha atual, e escolher de novo remove o formato.

## Busca

**NVDA+Alt+B** (ou Buscar… na janela) procura no título, no conteúdo e nas tags, sem diferenciar acentos e maiúsculas, enquanto você digita. Os resultados mostram título, trecho, relevância e data; Enter abre a folha. A busca leva uma fração de segundo mesmo com 100 mil folhas.

## Cadernos e pastas

A janela **Cadernos e pastas…** mostra cada pasta com os seus cadernos e as suas folhas, um ramo "Sem pasta" com os outros cadernos e um ramo "Folhas soltas". Enter abre uma folha. **Criar…** cria uma folha, um caderno ou uma pasta no lugar selecionado; **Renomear…** (F2) renomeia uma pasta ou um caderno ou muda o título de uma folha; **Mover para…** move uma folha ou um caderno; **Excluir** (tecla Delete) exclui. Excluir um caderno ou uma pasta nunca apaga folhas: elas ficam soltas.

## Exportar como documento

**Exportar…** (Alt+E) na janela principal abre um menu com **Folha selecionada…**, **Caderno…** e **Pasta…** e depois pergunta o formato: **Documento do Word (.docx)**, **Markdown (.md)** ou **Página HTML (.html)**. Um caderno ou uma pasta pode ir para **um arquivo com todas as folhas** ou para **um arquivo para cada folha** (numa pasta nova com o nome do caderno ou da pasta e uma subpasta para cada caderno). Cada folha leva título, status, tags, datas e o conteúdo com a formatação; os títulos são títulos de verdade, fáceis de navegar com o leitor de telas. Nada é sobrescrito sem perguntar, os arquivos são gravados em segundo plano e o NVDA fala quantas folhas foram exportadas e onde.

## Atalhos

| Atalho | Ação |
|---|---|
| NVDA+Alt+N | Abrir a janela Notas Workflow NVDA |
| NVDA+Alt+F | Nova folha |
| NVDA+Alt+B | Buscar nas folhas |
| Alt+Shift+Seta para a direita e para a esquerda | Status seguinte ou anterior da folha |
| Ctrl+Shift+Seta para cima e para baixo | Sobe ou desce a folha dentro da raia |
| Ctrl+S, Ctrl+B, Ctrl+I | Salvar, negrito e itálico na janela da folha |

Eles podem ser mudados em NVDA, Preferências, Definir comandos, categoria Notas Workflow NVDA, onde também há um comando, sem atalho, que diz quantas folhas cada raia tem.

## Onde ficam as folhas

No arquivo `NotasWorkflowNVDA-data.json` da pasta das folhas, por padrão a pasta `NotasWorkflowNVDA` dentro da pasta de configurações do NVDA (`%APPDATA%\nvda`). Em NVDA, Preferências, Configurações, categoria **Notas Workflow NVDA**, você muda a pasta: escolha uma pasta do OneDrive ou do Google Drive para computador para ter as folhas em todos os computadores. Ali também ficam o tempo do salvamento automático e **Importar folhas…** e **Exportar folhas…**.

Toda mudança é salva em segundo plano, de forma segura: o arquivo anterior fica guardado como `NotasWorkflowNVDA-data.json.bak`, e tudo o que estiver pendente é gravado antes de o NVDA fechar. Se o arquivo estiver danificado, ele é guardado com outro nome e a cópia de segurança é usada. Desinstalar o complemento não apaga as folhas.

## Muitas folhas

O complemento foi medido com 100 mil folhas: o NVDA inicia na hora (as folhas são lidas em segundo plano), e mudar o status, abrir uma folha, salvar e buscar levam frações de segundo.

## Privacidade

O complemento não usa a internet: nenhuma folha sai do computador, e o conteúdo das folhas nunca vai para o log do NVDA.
