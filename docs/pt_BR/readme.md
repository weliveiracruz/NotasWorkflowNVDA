# Notas Workflow NVDA

Complemento do NVDA com o mesmo fluxo de trabalho da aplicação web Notas Workflow: folhas organizadas em raias de status (A fazer, Em andamento, Bloqueada, Concluída), agrupadas em cadernos e pastas, com tags, conteúdo com formatação, salvamento automático e busca. Tudo funciona pelo teclado, com respostas faladas, sem navegador.

## A janela principal

Pressione **NVDA+Alt+N** (ou menu do NVDA, Ferramentas, **Notas Workflow NVDA…**). A janela tem:

* **Mostrar**: todas as folhas, folhas soltas (sem caderno), folhas recentes (as 10 alteradas por último), um caderno ou uma pasta.
* **Visualização**: **Raias (árvore)**, com um ramo por raia ("A fazer, 3 folhas"), ou **Tabela**, com as colunas Título, Status, Caderno, Tags e Atualizada em.
* **Folhas**: a lista em si. Enter abre a folha, Delete exclui (depois de confirmar), **Alt+Shift+Seta para a direita** move para a raia seguinte e **Alt+Shift+Seta para a esquerda** para a anterior.
* Botões **Nova folha…**, **Abrir**, **Mover para…** (menu com as outras raias), **Mudar caderno…**, **Excluir**, **Buscar…**, **Cadernos e pastas…** e **Fechar** (Esc).

## Folhas

**Nova folha** (NVDA+Alt+F ou o botão Nova folha…) pede o título, o caderno e o status e depois abre a janela da folha. A janela da folha tem título, caderno, status, tags (separadas por vírgula) e o conteúdo. Ela salva sozinha 2 segundos depois que você para de digitar; Ctrl+S salva na hora e fechar a janela (Esc ou Salvar e fechar) sempre salva. Nada se perde.

O conteúdo é texto com uma marcação leve, os mesmos formatos do editor web:

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

**NVDA+Alt+B** (ou Buscar… na janela) procura no título, no conteúdo e nas tags, sem diferenciar acentos e maiúsculas, enquanto você digita. Os resultados mostram título, trecho, relevância e data; Enter abre a folha.

## Cadernos e pastas

A janela **Cadernos e pastas…** mostra cada pasta com os seus cadernos e um ramo "Sem pasta". Ela cria cadernos (dentro da pasta selecionada) e pastas, renomeia (F2), move um caderno para outra pasta e exclui (Delete). Excluir um caderno ou uma pasta nunca apaga folhas: elas ficam soltas.

## Atalhos

| Atalho | Ação |
|---|---|
| NVDA+Alt+N | Abrir a janela Notas Workflow NVDA |
| NVDA+Alt+F | Nova folha |
| NVDA+Alt+B | Buscar nas folhas |
| Alt+Shift+Seta para a direita e para a esquerda | Mover a folha para a raia seguinte ou anterior |
| Ctrl+S, Ctrl+B, Ctrl+I | Salvar, negrito e itálico na janela da folha |

Eles podem ser mudados em NVDA, Preferências, Definir comandos, categoria Notas Workflow NVDA, onde também há um comando, sem atalho, que diz quantas folhas cada raia tem.

## Onde ficam as folhas

No arquivo `NotasWorkflowNVDA-data.json` da pasta das folhas, por padrão a pasta `NotasWorkflowNVDA` dentro da pasta de configurações do NVDA (`%APPDATA%\nvda`). Em NVDA, Preferências, Configurações, categoria **Notas Workflow NVDA**, você muda a pasta: escolha uma pasta do OneDrive ou do Google Drive para computador para ter as folhas em todos os computadores. Ali também ficam o tempo do salvamento automático e **Importar folhas…** e **Exportar folhas…**.

Toda mudança é salva na hora, de forma segura: o arquivo anterior fica guardado como `NotasWorkflowNVDA-data.json.bak`. Se o arquivo estiver danificado, ele é guardado com outro nome e a cópia de segurança é usada. Desinstalar o complemento não apaga as folhas.

## Folhas da aplicação web

Exportar e importar usam o formato da aplicação web (os mesmos campos de folhas, cadernos e pastas). Para trazer as folhas do navegador, abra a aplicação web, pressione F12, vá em Console e rode `copy(JSON.stringify({notes: JSON.parse(localStorage["notas-workflow:notes"] || "[]"), notebooks: JSON.parse(localStorage["notas-workflow:notebooks"] || "[]")}))`. Cole o texto em um arquivo terminado em `.json` e use **Importar folhas…**. Folhas com o mesmo identificador ficam com a versão alterada por último.

## Privacidade

O complemento não usa a internet: nenhuma folha sai do computador, e o conteúdo das folhas nunca vai para o log do NVDA.
