# Notas Workflow NVDA

## Sobre este manual

Este manual descreve, em detalhe, todas as funcionalidades do complemento **Notas Workflow NVDA** para o leitor de telas NVDA, versão {{versao}}. Ele é atualizado a cada nova versão do complemento.

O Notas Workflow NVDA leva para dentro do NVDA o mesmo fluxo de trabalho da aplicação web Notas Workflow: **folhas** (anotações) organizadas em **raias** de status, agrupadas em **cadernos** e **pastas**, com tags, conteúdo com formatação, salvamento automático e busca. Tudo funciona pelo teclado, com respostas faladas, sem navegador.

> **Dica:** os nomes de botões e campos deste manual são os da interface em português. Entre parênteses aparece a letra de atalho com Alt de cada um, por exemplo **Nova folha… (Alt+N)**.

## Conceitos

### Folha

Uma folha é uma anotação. Ela tem título, conteúdo, tags, uma raia (status), um caderno (opcional) e as datas de criação e da última alteração. A folha sem caderno é chamada de **folha solta**.

### Raias

As raias são as colunas de status do quadro, as mesmas da aplicação web, sempre nesta ordem:

| Raia | Uso sugerido |
|---|---|
| A fazer | O que ainda vai começar. É a raia padrão de uma folha nova. |
| Em andamento | O que está sendo feito agora. |
| Bloqueada | O que está parado esperando alguma coisa. |
| Concluída | O que terminou. |

No web cada raia tem uma cor. No complemento a raia é sempre dita pelo **nome**: a informação nunca depende de cor.

### Cadernos e pastas

Um **caderno** agrupa folhas, por exemplo "Trabalho" ou "Faculdade". Uma **pasta** agrupa cadernos, por exemplo a pasta "Projetos" com os cadernos "Site" e "Aplicativo". Uma folha pertence a no máximo um caderno, e um caderno a no máximo uma pasta.

### Tags

Tags são palavras livres que marcam a folha, como "urgente" ou "ideia". São digitadas separadas por vírgula, sem repetição (maiúsculas e minúsculas contam como a mesma tag), com no máximo 30 tags de até 50 caracteres cada.

## Instalação e requisitos

- NVDA 2024.1 ou mais novo (testado até o NVDA 2026.1.1).
- Windows 10 ou 11.
- Não precisa de internet, de conta nem de navegador.

Para instalar, abra o arquivo `NotasWorkflowNVDA-{{versao}}.nvda-addon` com o NVDA em execução, confirme a instalação e reinicie o NVDA quando ele pedir.

Para desinstalar, use o menu do NVDA, Ferramentas, Loja de complementos, aba Complementos instalados. **Desinstalar não apaga as suas folhas**: elas continuam na pasta das folhas (veja Onde ficam as folhas).

### Quem usava o NotasWorkflow 1.0.0

Até a versão 1.0.0, o complemento se chamava **NotasWorkflow**. A partir da 1.1.0 ele se chama **Notas Workflow NVDA**, e o NVDA o trata como um complemento novo, que fica instalado ao lado do antigo. Para trocar sem perder nada:

1. Instale o `NotasWorkflowNVDA-{{versao}}.nvda-addon` e reinicie o NVDA.
2. No primeiro início, o complemento copia as folhas da pasta antiga (`%APPDATA%\nvda\NotasWorkflow`) e as configurações (pasta das folhas, visualização, salvamento automático e anúncio). O NVDA fala "Folhas da versão anterior trazidas para o Notas Workflow NVDA" e o número de folhas.
3. Pressione **NVDA+Alt+N** e confira as suas folhas.
4. Desinstale o **NotasWorkflow** antigo na Loja de complementos e reinicie o NVDA. Enquanto os dois estiverem instalados, os atalhos NVDA+Alt+N, NVDA+Alt+F e NVDA+Alt+B ficam repetidos.

A migração só **copia**: o arquivo antigo `NotasWorkflow-data.json` continua onde estava e nunca é alterado nem apagado. Ela acontece uma única vez. Se você tinha escolhido uma pasta das folhas própria (por exemplo, no OneDrive), a mesma pasta continua em uso, e o arquivo antigo dela é copiado para o nome novo `NotasWorkflowNVDA-data.json`.

## Primeiros passos

1. Pressione **NVDA+Alt+N** para abrir a janela Notas Workflow NVDA. O foco fica na lista de folhas.
2. Pressione **Alt+N** (botão Nova folha…), digite o título e pressione **Enter**. O NVDA fala "Folha criada em A fazer".
3. A janela da folha abre com o foco no **Conteúdo**. Escreva o que quiser. A folha é salva sozinha 2 segundos depois que você para de digitar.
4. Pressione **Esc** para salvar e voltar para a lista. A folha nova está selecionada.
5. Com a folha selecionada, pressione **Alt+Shift+Seta para a direita** para movê-la para Em andamento. O NVDA fala "Movida para Em andamento".

## Janela Notas Workflow NVDA

Abra com **NVDA+Alt+N** ou pelo item **Notas Workflow NVDA…** do menu Ferramentas do NVDA. A janela é única: abrir de novo traz a mesma janela para a frente, com a mesma folha selecionada.

### Controles da janela

Os controles aparecem nesta ordem de tabulação:

| Controle | Atalho | O que faz |
|---|---|---|
| Mostrar | Alt+M | Escolhe quais folhas aparecem (veja Filtros). |
| Visualização | Alt+V | Escolhe entre **Raias (árvore)** e **Tabela**. A escolha fica lembrada. |
| Folhas | Alt+F | A lista de folhas. O rótulo diz o filtro e a quantidade, por exemplo "Folhas: Caderno: Trabalho (4)". |
| Nova folha… | Alt+N | Cria uma folha na raia selecionada (e no caderno, se o filtro for um caderno). |
| Abrir | Alt+A | Abre a folha selecionada. |
| Mover para… | Alt+P | Abre um menu com as outras raias e move a folha para a escolhida. |
| Mudar caderno… | Alt+C | Escolhe o caderno da folha, ou Folha solta (sem caderno). |
| Excluir | Alt+X | Exclui a folha selecionada, depois de confirmar. |
| Buscar… | Alt+B | Abre a janela Buscar folhas. |
| Cadernos e pastas… | Alt+T | Abre a janela Cadernos e pastas. |
| Fechar | Alt+H ou Esc | Fecha a janela. |

Os botões Abrir, Mover para…, Mudar caderno… e Excluir só ficam disponíveis (e só entram na tabulação) quando uma folha está selecionada.

### Visualização em raias (árvore)

Cada raia é um ramo já aberto, com o nome e o número de folhas, por exemplo "A fazer, 3 folhas". Dentro dele, cada folha é lida assim:

`Título, caderno Trabalho, tags urgente, cliente, atualizada em 12/10/2026`

O caderno e as tags só aparecem quando existem. Seta para cima e para baixo percorrem raias e folhas; Seta para a esquerda fecha uma raia e Seta para a direita abre.

### Visualização em tabela

Cada linha é uma folha, com as colunas **Título**, **Status**, **Caderno**, **Tags** e **Atualizada em**. As folhas seguem a ordem das raias. Folhas sem caderno mostram um traço na coluna Caderno.

### Teclas na lista de folhas

| Tecla | Ação |
|---|---|
| Enter | Abre a folha selecionada (na árvore, sobre uma raia, abre ou fecha a raia). |
| Delete | Exclui a folha selecionada, depois de confirmar. |
| Alt+Shift+Seta para a direita | Move a folha para a raia seguinte. |
| Alt+Shift+Seta para a esquerda | Move a folha para a raia anterior. |

Na primeira raia, mover para a anterior faz o NVDA dizer "Já está na primeira raia"; na última, "Já está na última raia". Depois de mover, a seleção acompanha a folha.

### Filtros

A caixa **Mostrar** oferece:

| Opção | Mostra |
|---|---|
| Todas as folhas | Todas as folhas. |
| Folhas soltas | As folhas sem caderno. |
| Folhas recentes | As 10 folhas alteradas por último, da mais nova para a mais antiga. |
| Caderno: nome | As folhas daquele caderno. Há uma opção para cada caderno. |
| Pasta: nome | As folhas dos cadernos daquela pasta. Há uma opção para cada pasta. |

## Criar uma folha

Use **NVDA+Alt+F** de qualquer lugar, ou o botão **Nova folha… (Alt+N)** da janela principal. A janela Nova folha tem:

| Campo | Atalho | Descrição |
|---|---|---|
| Título | Alt+T | Obrigatório, até 200 caracteres. |
| Caderno | Alt+D | Folha solta (sem caderno) ou um dos cadernos. |
| Status | Alt+S | A raia: A fazer, Em andamento, Bloqueada ou Concluída. |
| Criar folha | Alt+R ou Enter | Cria a folha. Fica indisponível enquanto o título estiver vazio. |
| Cancelar | Esc | Fecha sem criar nada. |

Depois de criar, o NVDA fala "Folha criada em" e o nome da raia, e a janela da folha abre com o foco no conteúdo.

## Janela da folha

Abre com **Enter** ou **Abrir (Alt+A)** em uma folha, ou logo depois de criar uma. O título da janela é o título da folha.

### Campos

| Campo | Atalho | Descrição |
|---|---|---|
| Título | Alt+T | O título da folha. Uma folha sem título aparece como "Sem título". |
| Caderno | Alt+D | Muda o caderno da folha. |
| Status | Alt+S | Muda a raia da folha. |
| Tags (separadas por vírgula) | Alt+G | Por exemplo: urgente, cliente, ideia. |
| Conteúdo | Alt+C | O texto da folha, com várias linhas e a marcação de formatação. |
| Formatação… | Alt+F | Abre o menu de formatos (veja Formatação do conteúdo). |
| Situação do salvamento | Alt+I | Campo somente leitura que diz se tudo está salvo. |
| Salvar e fechar | Alt+L | Salva o que estiver pendente e fecha. |

### Salvamento automático

Ao digitar, a Situação do salvamento passa a "Alterações não salvas…". Dois segundos depois da última tecla (tempo ajustável nas configurações), a folha é salva e a situação muda para "Salva às" e a hora.

| Situação | Significado |
|---|---|
| Salva | Nada mudou desde que a janela abriu. |
| Alterações não salvas… | Há mudanças esperando o salvamento automático. |
| Salva às 14:32 | Tudo salvo, por último naquele horário. |
| Não salva | A gravação falhou (veja Mensagens faladas). A próxima mudança tenta de novo. |

**Nada se perde:** Ctrl+S salva na hora (o NVDA fala "Folha salva"), e fechar a janela por Esc, por Salvar e fechar ou pelo botão de fechar sempre salva o que estiver pendente. Até se o NVDA for encerrado com a janela aberta, o que foi digitado é salvo.

Só os campos que você mudou são gravados. Uma folha criada na aplicação web mantém o HTML original enquanto você não mexer no conteúdo.

## Formatação do conteúdo

O conteúdo é texto com uma marcação leve, fácil de ler com o NVDA. O complemento converte essa marcação para o formato do editor web (HTML do TipTap) e de volta, sem perder nada.

### Marcação

| Digite | Para ter |
|---|---|
| `## Título` | Título 2 |
| `### Título` | Título 3 |
| `- item` | Lista com marcadores |
| `1. item` | Lista numerada |
| `> texto` | Citação |
| `---` | Divisor (linha horizontal) |
| `**texto**` | Negrito |
| `*texto*` | Itálico |
| `~~texto~~` | Tachado |
| `` `texto` `` | Código |
| uma linha só com três crases antes do código e outra depois | Bloco de código |

Cada linha vira um parágrafo; uma linha vazia vira um parágrafo vazio. O asterisco só vira itálico no começo e no fim de palavras: `2*3*4` continua igual.

### Menu Formatação e atalhos

O botão **Formatação… (Alt+F)** abre um menu com: Negrito (Ctrl+B), Itálico (Ctrl+I), Tachado, Código, Título 2, Título 3, Lista com marcadores, Lista numerada, Citação e Divisor.

- Negrito, Itálico, Tachado e Código valem para o **texto selecionado**. Sem seleção, as marcas são inseridas e o cursor fica entre elas, pronto para digitar.
- Título 2, Título 3, as listas e a Citação valem para a **linha atual** ou para todas as linhas selecionadas. A Lista numerada numera as linhas em sequência.
- Divisor insere uma linha `---` própria na posição do cursor.
- Escolher de novo um formato já aplicado o **remove**: o NVDA fala, por exemplo, "Negrito removido".
- No campo Conteúdo, **Ctrl+B** e **Ctrl+I** aplicam negrito e itálico sem abrir o menu.

### Exemplo

O texto abaixo, digitado no Conteúdo:

`## Reunião de segunda`

`- revisar o **orçamento**`

`- marcar *demo* com o cliente`

aparece na aplicação web como um título, seguido de uma lista com dois itens, com "orçamento" em negrito e "demo" em itálico.

## Mover, mudar caderno e excluir

### Mover entre raias

Há duas formas, as mesmas da aplicação web:

- **Alt+Shift+Seta para a direita ou para a esquerda** na lista: raia seguinte ou anterior.
- **Mover para… (Alt+P)**: um menu com as três outras raias.

O NVDA fala "Movida para" e o nome da raia, e a seleção acompanha a folha. Também é possível mudar a raia pelo campo Status da janela da folha.

### Mudar o caderno

**Mudar caderno… (Alt+C)** mostra a lista "Folha solta (sem caderno)" e os cadernos. O NVDA confirma com "Movida para o caderno" e o nome, ou "Agora é uma folha solta". Se o filtro atual deixar de mostrar a folha, a seleção vai para a vizinha.

### Excluir

**Excluir (Alt+X)** ou a tecla **Delete** perguntam "Excluir a folha …? Isso não pode ser desfeito.", com **Não** como resposta padrão. Ao confirmar, o NVDA fala "Folha excluída:" e o título, e a seleção vai para a folha vizinha.

## Buscar folhas

Use **NVDA+Alt+B** de qualquer lugar, ou **Buscar… (Alt+B)** na janela principal.

| Controle | Atalho | Descrição |
|---|---|---|
| Buscar | Alt+B | Digite as palavras. A busca roda sozinha 300 milissegundos depois que você para de digitar; Enter busca na hora e leva o foco aos resultados. |
| Resultados | Alt+R | Tabela com Título, Trecho, Relevância e Atualizada em. O rótulo diz quantos resultados há. Enter abre a folha. |
| Abrir | Alt+A | Abre a folha selecionada nos resultados. |
| Fechar | Alt+H ou Esc | Fecha a busca. |

Como a busca funciona:

- Procura no título, no conteúdo (sem a marcação) e nas tags.
- Não diferencia acentos nem maiúsculas: "acao" encontra "Ação".
- A **relevância** é a porcentagem das palavras buscadas que a folha contém. Em caso de empate, vêm primeiro as folhas com as palavras no título e, depois, as alteradas por último.
- O **trecho** mostra até 120 caracteres em volta da primeira palavra encontrada.
- Aparecem no máximo 100 resultados.
- O NVDA fala "Encontrado:" e o número de folhas, ou "Nenhuma folha encontrada".

Ao voltar de uma folha aberta pela busca, os resultados são atualizados e a folha continua selecionada.

## Cadernos e pastas

Abra pelo botão **Cadernos e pastas… (Alt+T)** da janela principal.

### A árvore Organização

A árvore **Organização (Alt+O)** mostra cada pasta com os seus cadernos, por exemplo "Pasta Projetos, 2 cadernos", e no fim o ramo "Sem pasta" com os cadernos que não estão em nenhuma pasta. Cada caderno diz quantas folhas tem, por exemplo "Trabalho, 4 folhas".

### Botões

| Botão | Atalho | O que faz |
|---|---|---|
| Novo caderno… | Alt+C | Cria um caderno. Se uma pasta (ou um caderno dentro dela) estiver selecionada, o caderno nasce dentro dessa pasta. |
| Nova pasta… | Alt+P | Cria uma pasta. |
| Renomear… | Alt+R ou F2 | Renomeia a pasta ou o caderno selecionado. |
| Mover para pasta… | Alt+M | Move o caderno selecionado para outra pasta ou para Sem pasta. |
| Excluir | Alt+X ou Delete | Exclui a pasta ou o caderno selecionado, depois de confirmar. |
| Fechar | Alt+H ou Esc | Fecha a janela. |

Excluir **nunca apaga folhas**: ao excluir um caderno, as folhas dele viram folhas soltas; ao excluir uma pasta, os cadernos e as folhas dela ficam sem pasta. Nomes têm até 100 caracteres e não podem ficar vazios. As opções da caixa Mostrar acompanham os cadernos e pastas criados, renomeados e excluídos.

## Configurações

Abra o menu do NVDA, Preferências, Configurações, categoria **Notas Workflow NVDA**.

| Opção | Atalho | Descrição |
|---|---|---|
| Pasta das folhas | Alt+P | A pasta onde fica o arquivo das folhas. |
| Procurar… | Alt+R | Escolhe a pasta numa janela do Windows. |
| Usar a pasta padrão | Alt+D | Volta para a pasta padrão. |
| Salvar automaticamente depois de (segundos) | Alt+S | De 1 a 30 segundos. Padrão: 2. |
| Anunciar o salvamento automático | Alt+A | Quando marcada, o NVDA fala "Folha salva" a cada salvamento automático. Vem desmarcada para não interromper a digitação. |
| Importar folhas… | Alt+I | Traz folhas de um arquivo (veja Importar e exportar). |
| Exportar folhas… | Alt+E | Grava todas as folhas num arquivo. |

Ao trocar a pasta das folhas e pressionar OK:

- se a pasta nova **já tem** folhas do Notas Workflow NVDA, elas passam a ser usadas ("Usando as folhas da nova pasta");
- se a pasta nova **está vazia**, as folhas atuais são gravadas nela ("Folhas salvas na nova pasta").

A pasta precisa existir e poder ser gravada; senão, as configurações avisam e não fecham.

## Onde ficam as folhas

As folhas ficam no arquivo `NotasWorkflowNVDA-data.json`, na pasta das folhas. A pasta padrão é a subpasta `NotasWorkflowNVDA` da pasta de configurações do NVDA, normalmente `%APPDATA%\nvda\NotasWorkflowNVDA`. Na versão portátil do NVDA, fica dentro da pasta do NVDA portátil.

### Segurança dos dados

- Toda mudança é gravada na hora, de forma segura: o complemento escreve um arquivo temporário e só então troca pelo arquivo antigo, que fica guardado como cópia de segurança `NotasWorkflowNVDA-data.json.bak`.
- Se o arquivo estiver danificado, ele é guardado com outro nome (`NotasWorkflowNVDA-data.corrupt-` seguido da data) e a cópia de segurança é usada. O NVDA avisa. Nenhum arquivo é apagado.
- Se não for possível gravar (disco cheio, pasta sem permissão), as folhas continuam abertas, o NVDA avisa e a próxima mudança tenta de novo.

### Usar em mais de um computador

Escolha como pasta das folhas uma pasta do **OneDrive** ou do **Google Drive para computador**. Esses programas sincronizam o arquivo sozinhos. Ao abrir a janela Notas Workflow NVDA, o complemento percebe se o arquivo foi mudado em outro computador e lê as folhas de novo.

> **Atenção:** se dois computadores mudarem as folhas ao mesmo tempo, vale a última gravação. A cópia de segurança `.bak` guarda a versão anterior.

## Importar e exportar

### Exportar

**Exportar folhas… (Alt+E)** nas configurações grava todas as folhas, cadernos e pastas num arquivo `.json`, no mesmo formato da aplicação web. O NVDA fala "Exportado:" e o número de folhas.

### Importar

**Importar folhas… (Alt+I)** junta as folhas de um arquivo às suas:

- folhas, cadernos e pastas novos são acrescentados;
- quando o arquivo traz uma folha que você já tem (mesmo identificador), fica a versão alterada por último;
- dados inválidos são corrigidos ou descartados, e arquivos acima de 20 MB não são abertos.

O NVDA fala "Importado:" com o número de folhas, cadernos e pastas trazidos.

### Trazer as folhas da aplicação web

1. Abra a aplicação web Notas Workflow no navegador.
2. Pressione F12 e vá na aba Console.
3. Cole e execute: `copy(JSON.stringify({notes: JSON.parse(localStorage["notas-workflow:notes"] || "[]"), notebooks: JSON.parse(localStorage["notas-workflow:notebooks"] || "[]")}))`
4. Abra o Bloco de Notas, cole (Ctrl+V) e salve como `folhas.json`.
5. No NVDA, use **Importar folhas…** e escolha o arquivo.

## Atalhos

### Comandos globais

| Atalho | Ação |
|---|---|
| NVDA+Alt+N | Abrir a janela Notas Workflow NVDA |
| NVDA+Alt+F | Nova folha |
| NVDA+Alt+B | Buscar nas folhas |
| sem atalho | Falar quantas folhas cada raia tem (por exemplo "A fazer 2, Em andamento 1, Bloqueada 0, Concluída 3") |

Todos podem ser mudados em NVDA, Preferências, Definir comandos, categoria **Notas Workflow NVDA**, onde também dá para dar um atalho ao resumo das raias.

### Dentro das janelas

| Atalho | Onde | Ação |
|---|---|---|
| Enter | Lista de folhas, resultados | Abrir a folha |
| Delete | Lista de folhas, Organização | Excluir |
| Alt+Shift+Seta para a direita | Lista de folhas | Mover para a raia seguinte |
| Alt+Shift+Seta para a esquerda | Lista de folhas | Mover para a raia anterior |
| F2 | Organização | Renomear |
| Ctrl+S | Janela da folha | Salvar agora |
| Ctrl+B | Conteúdo | Negrito |
| Ctrl+I | Conteúdo | Itálico |
| Esc | Qualquer janela | Fechar (na janela da folha, salva antes) |

## Mensagens faladas

| O NVDA fala | Quando |
|---|---|
| Folha criada em A fazer | Uma folha foi criada (com o nome da raia escolhida). |
| Movida para Em andamento | A folha mudou de raia. |
| Já está na primeira raia / Já está na última raia | Não há raia anterior ou seguinte. |
| Movida para o caderno Trabalho / Agora é uma folha solta | O caderno da folha mudou. |
| Folha excluída: título | A folha foi excluída. |
| Folha salva | Ctrl+S, ou o salvamento automático com o anúncio ligado. |
| Negrito, Lista numerada… / Negrito removido | Um formato foi aplicado ou removido. |
| Encontrado: 3 folhas / Nenhuma folha encontrada | Resultado da busca. |
| Caderno … criado, Pasta … criada, Renomeado para …, Movido para …, … excluído | Ações em Cadernos e pastas. |
| Importado: … / Exportado: … | Importação e exportação. |
| Folhas salvas na nova pasta / Usando as folhas da nova pasta | A pasta das folhas mudou. |
| Folhas da versão anterior trazidas para o Notas Workflow NVDA: 2 folhas… | Primeiro início depois de trocar o NotasWorkflow 1.0.0 pelo Notas Workflow NVDA. |
| Esta folha foi excluída. | A folha aberta foi excluída por outro caminho; nada é recriado. |
| As folhas salvas estavam danificadas… | O arquivo estava danificado; foi guardado com outro nome. |
| Não foi possível salvar as folhas em … | Erro de gravação: confira a pasta. |
| Este arquivo não tem folhas do Notas Workflow NVDA. | O arquivo escolhido para importar não é válido. |
| O arquivo tem mais de 20 MB e não foi aberto. | Arquivo grande demais. |
| O nome não pode ficar vazio. | Caderno ou pasta sem nome. |

## Privacidade e segurança

- O complemento **não usa a internet**: nenhuma folha sai do computador, e não há conta nem senha.
- O título, o conteúdo e as tags das folhas **nunca** vão para o log do NVDA.
- Excluir sempre pede confirmação, com Não como padrão; excluir caderno ou pasta nunca apaga folhas.
- Arquivos importados são conferidos: tamanhos, tipos e identificadores inválidos são corrigidos ou descartados, e o HTML nunca é exibido nem executado.
- O complemento fica desligado nas telas seguras do Windows (tela de logon e controle de conta de usuário).
- As folhas ficam num arquivo de texto legível na pasta do seu perfil do Windows, como no navegador na aplicação web.

## Perguntas frequentes

### O NVDA diz que não foi possível salvar as folhas

A pasta das folhas não existe mais ou não pode ser gravada (por exemplo, um pen drive removido). Escolha outra pasta nas configurações ou use **Usar a pasta padrão**. As folhas abertas continuam na memória até lá.

### Minhas folhas sumiram depois de trocar a pasta

A pasta nova já tinha folhas do Notas Workflow NVDA, e elas passaram a ser usadas. Volte à pasta anterior nas configurações: as folhas antigas continuam lá.

### O arquivo estava danificado

O complemento guardou o arquivo danificado com o nome `NotasWorkflowNVDA-data.corrupt-` seguido da data e usou a cópia de segurança. Se quiser, envie o arquivo guardado para análise; ele nunca é apagado.

### Escrevi um asterisco e ele sumiu na aplicação web

Pares de asteriscos em volta de uma palavra viram itálico (`*palavra*`). Para mostrar asteriscos, use-os no meio de palavras ou números, como `2*3`.

### Como vejo a cor da raia?

O complemento diz sempre o nome da raia; as cores existem só para a aplicação web e são mantidas no arquivo.

## Histórico deste manual

| Versão | Mudanças |
|---|---|
| 1.0.0 | Primeira versão do manual, com todas as funcionalidades da versão 1.0.0 do complemento. |
| 1.1.0 | Novo nome do complemento, Notas Workflow NVDA, com os novos nomes de pasta e arquivo; nova seção "Quem usava o NotasWorkflow 1.0.0" com a migração das folhas; nova mensagem falada da migração. |
