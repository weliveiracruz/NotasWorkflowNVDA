# Notas Workflow NVDA

## Sobre este manual

Este manual descreve, em detalhe, todas as funcionalidades do complemento **Notas Workflow NVDA** para o leitor de telas NVDA, versão {{versao}}. Ele é atualizado a cada nova versão do complemento.

O Notas Workflow NVDA organiza **folhas** (anotações e tarefas) em **raias** de status, agrupadas em **cadernos** e **pastas**, com tags, conteúdo com formatação, salvamento automático e busca. Tudo funciona pelo teclado, com respostas faladas, e continua rápido mesmo com dezenas de milhares de folhas.

> **Dica:** os nomes de botões e campos deste manual são os da interface em português. Entre parênteses aparece a letra de atalho com Alt de cada um, por exemplo **Criar… (Alt+C)**.

## Conceitos

### Folha

Uma folha é uma anotação ou tarefa. Ela tem título, conteúdo, tags, um status (a raia), um local (um caderno, uma pasta ou nenhum) e as datas de criação e da última alteração. A folha que não está em nenhum caderno nem em nenhuma pasta é chamada de **folha solta**.

### Raias (status)

As raias são os status das tarefas, sempre nesta ordem:

| Raia | Uso sugerido |
|---|---|
| A fazer | O que ainda vai começar. É o status padrão de uma folha nova. |
| Em andamento | O que está sendo feito agora. |
| Bloqueada | O que está parado esperando alguma coisa. |
| Concluída | O que terminou. |

A raia é sempre dita pelo **nome**: a informação nunca depende de cor.

### Cadernos e pastas

Um **caderno** agrupa folhas, por exemplo "Trabalho" ou "Faculdade". Uma **pasta** agrupa cadernos e também pode guardar folhas diretamente, por exemplo a pasta "Projetos" com os cadernos "Site" e "Aplicativo" e algumas folhas gerais. Uma folha fica em no máximo um lugar: num caderno, direto numa pasta ou solta. Um caderno fica em no máximo uma pasta.

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
2. No primeiro início, o complemento copia as folhas da pasta antiga (`%APPDATA%\nvda\NotasWorkflow`) e as configurações (pasta das folhas, salvamento automático e anúncio). O NVDA fala "Folhas da versão anterior trazidas para o Notas Workflow NVDA" e o número de folhas.
3. Pressione **NVDA+Alt+N** e confira as suas folhas.
4. Desinstale o **NotasWorkflow** antigo na Loja de complementos e reinicie o NVDA. Enquanto os dois estiverem instalados, os atalhos NVDA+Alt+N, NVDA+Alt+F e NVDA+Alt+B ficam repetidos.

A migração só **copia**: o arquivo antigo `NotasWorkflow-data.json` continua onde estava e nunca é alterado nem apagado. Ela acontece uma única vez. Se você tinha escolhido uma pasta das folhas própria (por exemplo, no OneDrive), a mesma pasta continua em uso, e o arquivo antigo dela é copiado para o nome novo `NotasWorkflowNVDA-data.json`.

## Primeiros passos

1. Pressione **NVDA+Alt+N** para abrir a janela Notas Workflow NVDA. O foco fica na lista de folhas, na primeira raia. As raias começam fechadas: **Seta para a direita** abre uma raia e mostra as folhas dela.
2. Pressione **Alt+C** (botão Criar…) e escolha **Folha…** no menu. Digite o título e pressione **Enter**. O NVDA fala "Folha criada em A fazer".
3. A janela da folha abre com o foco no **Conteúdo**. Escreva o que quiser. A folha é salva sozinha 2 segundos depois que você para de digitar.
4. Pressione **Esc** para salvar e voltar para a lista. A folha nova está selecionada.
5. Com a folha selecionada, pressione **Alt+Shift+Seta para a direita** para mudar o status para Em andamento. O NVDA fala "Status atualizado para Em andamento".
6. Pressione **Enter** sobre a folha para abri-la de novo.

## Janela Notas Workflow NVDA

Abra com **NVDA+Alt+N** ou pelo item **Notas Workflow NVDA…** do menu Ferramentas do NVDA. A janela é única: abrir de novo traz a mesma janela para a frente, na mesma folha. Fechar só esconde a janela, então reabrir é instantâneo.

### Controles da janela

Os controles aparecem nesta ordem de tabulação:

| Controle | Atalho | O que faz |
|---|---|---|
| Mostrar | Alt+O | Escolhe quais folhas aparecem (veja Filtros). |
| Folhas | Alt+F | A lista de folhas em raias. O rótulo diz o filtro e a quantidade, por exemplo "Folhas: Caderno: Trabalho (4)". Enter abre a folha selecionada. |
| Criar… | Alt+C | Abre um menu para criar uma **Folha…**, um **Caderno…** ou uma **Pasta…** (veja Criar folhas, cadernos e pastas). |
| Atualizar o status da tarefa… | Alt+A | Abre um menu com os outros status e muda o status da folha selecionada. |
| Mover para… | Alt+M | Move a folha selecionada para um caderno, para uma pasta ou a deixa solta. |
| Excluir | Alt+X | Exclui a folha selecionada, depois de confirmar. |
| Buscar… | Alt+B | Abre a janela Buscar folhas. |
| Cadernos e pastas… | Alt+T | Abre a janela Cadernos e pastas, que também lista e abre as folhas. |
| Exportar… | Alt+E | Exporta a folha selecionada, um caderno ou uma pasta como documento do Word, Markdown ou HTML (veja Exportar como documento). |
| Fechar | Alt+H ou Esc | Fecha a janela. |

Os botões Atualizar o status da tarefa…, Mover para… e Excluir só ficam disponíveis (e só entram na tabulação) quando uma folha está selecionada.

### A lista de folhas em raias

As raias **começam fechadas**: cada uma é um ramo com o nome e o número de folhas, por exemplo "A fazer, 3 folhas", e você só ouve as folhas da raia que abrir. Dentro de uma raia aberta, cada folha é lida assim:

`Título, caderno Trabalho, tags urgente, cliente, atualizada em 12/10/2026`

O local (caderno ou pasta) e as tags só aparecem quando existem. Seta para cima e para baixo percorrem raias e folhas; **Seta para a direita abre** uma raia e **Seta para a esquerda fecha**. Quando uma folha é selecionada pelo complemento (ao criar uma folha, ao voltar da busca, ao mudar o status), a raia dela abre sozinha. Enquanto a janela estiver aberta, as raias ficam como você as deixou.

### Listas longas

Para a janela continuar rápida com muitas folhas, cada raia mostra **200 folhas por vez**. Quando há mais, o último item da raia é "Mostrar mais 200 folhas (N ainda não mostradas)": pressione **Enter** nele para ver as próximas, e o foco vai para a primeira delas. Uma folha aberta pela busca ou escolhida em outro lugar sempre aparece, mesmo que esteja além das primeiras 200.

### Teclas na lista de folhas

| Tecla | Ação |
|---|---|
| Enter | Abre a folha selecionada. Numa raia, abre ou fecha a raia; em "Mostrar mais", mostra as próximas folhas. |
| Delete | Exclui a folha selecionada, depois de confirmar. |
| Alt+Shift+Seta para a direita | Muda o status da folha para o seguinte. |
| Alt+Shift+Seta para a esquerda | Muda o status da folha para o anterior. |

No primeiro status, ir para o anterior faz o NVDA dizer "Já está na primeira raia"; no último, "Já está na última raia". Depois da mudança, a seleção acompanha a folha.

### Filtros

A caixa **Mostrar** oferece:

| Opção | Mostra |
|---|---|
| Todas as folhas | Todas as folhas. |
| Folhas soltas | As folhas que não estão em nenhum caderno nem em nenhuma pasta. |
| Folhas recentes | As 10 folhas alteradas por último. |
| Caderno: nome | As folhas daquele caderno. Há uma opção para cada caderno. |
| Pasta: nome | As folhas guardadas direto na pasta e as dos cadernos dela. Há uma opção para cada pasta. |

## Criar folhas, cadernos e pastas

O botão **Criar… (Alt+C)** abre um menu com três opções:

| Opção | O que acontece |
|---|---|
| Folha… | Abre a janela Nova folha. A folha começa no status selecionado na lista e no caderno ou na pasta do filtro em uso. |
| Caderno… | Pede o nome do caderno. Se o filtro em uso for uma pasta, o caderno nasce dentro dela. O NVDA fala "Caderno … criado". |
| Pasta… | Pede o nome da pasta. O NVDA fala "Pasta … criada". |

Também é possível criar uma folha de qualquer lugar com **NVDA+Alt+F**. A janela Nova folha tem:

| Campo | Atalho | Descrição |
|---|---|---|
| Título | Alt+T | Obrigatório, até 200 caracteres. |
| Local | Alt+O | Folha solta (sem caderno nem pasta), uma pasta ou um caderno. Os cadernos aparecem com a pasta deles, por exemplo "Caderno Site (pasta Projetos)". |
| Status | Alt+S | A Fazer, Em andamento, Bloqueada ou Concluída. |
| Criar | Alt+R ou Enter | Cria a folha. Fica indisponível enquanto o título estiver vazio. |
| Cancelar | Esc | Fecha sem criar nada. |

Depois de criar, o NVDA fala "Folha criada em" e o nome do status, e a janela da folha abre com o foco no conteúdo. Nomes de cadernos e pastas têm até 100 caracteres e não podem ficar vazios.

## Janela da folha

Abre com **Enter** sobre uma folha (na lista, na busca ou em Cadernos e pastas), ou logo depois de criar uma. O título da janela é o título da folha.

### Campos

| Campo | Atalho | Descrição |
|---|---|---|
| Título | Alt+T | O título da folha. Uma folha sem título aparece como "Sem título". |
| Local | Alt+O | Muda o caderno ou a pasta da folha. |
| Status | Alt+S | Muda o status da folha. |
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

Só os campos que você mudou são gravados. Uma folha importada mantém o conteúdo original enquanto você não mexer nele.

## Formatação do conteúdo

O conteúdo é texto com uma marcação leve, fácil de ler com o NVDA. O complemento guarda essa marcação como texto formatado (títulos, listas, negrito…) e a mostra de volta do mesmo jeito, sem perder nada.

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

vira um título, seguido de uma lista com dois itens, com "orçamento" em negrito e "demo" em itálico.

## Status, local e exclusão

### Atualizar o status da tarefa

Há duas formas:

- **Alt+Shift+Seta para a direita ou para a esquerda** na lista: status seguinte ou anterior.
- **Atualizar o status da tarefa… (Alt+A)**: um menu com os três outros status.

O NVDA fala "Status atualizado para" e o nome do status, e a seleção acompanha a folha.

### Trabalhar a pilha de uma raia

Também é possível mudar o status (ou o local) pelos campos **Status** e **Local** da janela da folha. Nesse caso, ao fechar a janela da folha, o foco **não acompanha a folha movida**: ele vai para a **próxima folha da mesma raia**, a seguinte na pilha. Assim dá para tratar uma raia em sequência: Enter na primeira folha, mudar o status, Esc, e o foco já está na folha seguinte.

- Se a folha movida era a última da raia, o foco vai para a anterior.
- Se era a única, o foco vai para a própria raia.
- Se você só editou a folha, sem mudar o status nem a tirar do que está sendo mostrado, o foco volta para ela.

### Mover para um caderno ou uma pasta

**Mover para… (Alt+M)** mostra uma lista com todos os lugares possíveis, começando no lugar atual da folha:

- Folha solta (sem caderno nem pasta);
- cada pasta ("Pasta Projetos"), para guardar a folha direto nela;
- cada caderno, com a pasta dele ("Caderno Site (pasta Projetos)").

O NVDA confirma com "Agora em:" e o lugar escolhido. Se o filtro em uso deixar de mostrar a folha, a seleção vai para a folha vizinha. O mesmo botão existe na janela Cadernos e pastas, e o campo Local da janela da folha faz o mesmo.

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
- É rápida mesmo com 100 mil folhas: o texto de cada folha é preparado uma vez, logo depois que o NVDA inicia, e só é preparado de novo quando a folha muda.

Ao voltar de uma folha aberta pela busca, os resultados são atualizados e a folha continua selecionada.

## Cadernos e pastas

Abra pelo botão **Cadernos e pastas… (Alt+T)** da janela principal.

### A árvore Organização

A árvore **Organização (Alt+O)** mostra tudo, com as folhas dentro de cada lugar:

- cada pasta, por exemplo "Pasta Projetos, 2 cadernos, 3 folhas", com os cadernos dela e depois as folhas guardadas direto nela;
- cada caderno, por exemplo "Trabalho, 4 folhas", com as folhas dele;
- o ramo "Sem pasta", com os cadernos que não estão em nenhuma pasta;
- o ramo "Folhas soltas", com as folhas que não estão em nenhum caderno nem em nenhuma pasta.

Cada folha é lida com o título, o status, as tags e a data. **Enter sobre uma folha abre a folha.** As folhas de um caderno ou pasta só são carregadas quando você abre o ramo, 200 por vez, com o item "Mostrar mais" no fim, como na janela principal.

### Botões

| Botão | Atalho | O que faz |
|---|---|---|
| Criar… | Alt+C | Menu com Folha…, Caderno… e Pasta…. A folha nasce no caderno ou na pasta selecionada; o caderno nasce na pasta selecionada. |
| Renomear… | Alt+R ou F2 | Renomeia a pasta ou o caderno selecionado; numa folha, muda o título. |
| Mover para… | Alt+M | Numa folha, move para um caderno, uma pasta ou a deixa solta; num caderno, move para outra pasta ou para Sem pasta. |
| Excluir | Alt+X ou Delete | Exclui a pasta, o caderno ou a folha selecionada, depois de confirmar. |
| Fechar | Alt+H ou Esc | Fecha a janela. |

Excluir uma pasta ou um caderno **nunca apaga folhas**: ao excluir um caderno, as folhas dele viram folhas soltas; ao excluir uma pasta, os cadernos e as folhas dela ficam sem pasta. As opções da caixa Mostrar acompanham os cadernos e pastas criados, renomeados e excluídos.

## Exportar como documento

O botão **Exportar… (Alt+E)** da janela principal grava folhas como documentos para ler, imprimir ou enviar a outras pessoas: um documento do **Word**, um arquivo **Markdown** ou uma **página HTML**, que abre em qualquer navegador. É diferente de Exportar folhas… das configurações, que grava a cópia de segurança `.json` (veja Importar e exportar).

### O que exportar

O botão abre um menu com:

| Opção | O que exporta |
|---|---|
| Folha selecionada… | A folha selecionada na lista. Só aparece quando uma folha está selecionada. |
| Caderno… | Todas as folhas de um caderno. Uma lista pergunta qual caderno, começando no caderno mostrado na caixa Mostrar ou no caderno da folha selecionada. |
| Pasta… | Todas as folhas de uma pasta: as guardadas direto nela e as dos cadernos dela. Uma lista pergunta qual pasta, começando na pasta mostrada ou na pasta da folha selecionada. |

Se não houver nenhum caderno (ou nenhuma pasta), o NVDA fala "Não há cadernos." (ou "Não há pastas."). Um caderno ou uma pasta sem folhas não é exportado: o NVDA fala "Nada para exportar:" e o nome.

### Formato e arquivos

Depois, uma lista pergunta o formato:

| Formato | Arquivo | Bom para |
|---|---|---|
| Documento do Word (.docx) | `.docx` | Abrir no Word, no LibreOffice ou no Google Docs, imprimir e enviar. |
| Markdown (.md) | `.md` | Texto simples com marcação, para outros programas de anotações. |
| Página HTML (.html) | `.html` | Abrir no navegador, sem nenhum programa a mais. |

Num caderno ou numa pasta, outra lista pergunta como exportar:

- **Um arquivo com todas as folhas**: uma janela do Windows pergunta o nome e o lugar do arquivo, já com o nome do caderno ou da pasta. Se o arquivo já existe, o Windows pergunta antes de substituir.
- **Um arquivo para cada folha**: uma janela do Windows pergunta em que pasta gravar. O complemento cria ali uma pasta nova com o nome do caderno ou da pasta e grava um arquivo para cada folha, com o título da folha como nome. Numa pasta, as folhas de cada caderno ficam numa subpasta com o nome do caderno. **Nada é sobrescrito**: se a pasta "Trabalho" já existe, a nova se chama "Trabalho (2)"; duas folhas com o mesmo título viram "Título.md" e "Título (2).md". Caracteres que o Windows não aceita em nomes de arquivo são tirados do nome.

Para uma folha só, o complemento pergunta apenas o formato e o arquivo.

A gravação acontece em segundo plano, então o NVDA continua respondendo mesmo com milhares de folhas. Ao terminar, o NVDA fala, por exemplo, "Exportado: 3 folhas, em Trabalho.docx" ou "Exportado: 12 folhas, um arquivo por folha, na pasta" e o caminho. Se não for possível gravar (pasta sem permissão, disco cheio), o NVDA fala "Não foi possível exportar para" e o caminho.

### Como fica o documento

- Um caderno exportado num arquivo só começa com o título 1 "Caderno" e o nome, seguido da frase "Exportado do Notas Workflow NVDA em" com a data e o número de folhas. Cada folha é um **título 2**.
- Uma pasta começa com o título 1 "Pasta" e o nome. As folhas guardadas direto nela ficam sob o título 2 "Folhas direto na pasta", e as de cada caderno sob o título 2 "Caderno" e o nome; cada folha é um **título 3**.
- Uma folha sozinha (ou cada arquivo de "um arquivo para cada folha") tem o título da folha como **título 1**.
- As folhas aparecem na ordem das raias: A fazer, Em andamento, Bloqueada e Concluída.
- Logo abaixo do título de cada folha vêm as linhas **Status:**, **Tags:** (quando há tags) e **Criada em … , atualizada em …**. Na exportação de uma folha só, vem também **Local:** com o caderno ou a pasta.
- O conteúdo mantém a formatação: negrito, itálico, tachado, código, listas com marcadores e numeradas, citações, blocos de código e divisores. Os títulos do conteúdo ficam um nível abaixo do título da folha, para a estrutura de títulos continuar em ordem.

O documento é feito para leitores de telas: no Word, os títulos usam os estilos Título 1, Título 2… e aparecem no painel de navegação; na página HTML, são títulos de verdade, navegáveis com a tecla H do NVDA. O documento tem o idioma do NVDA e o título nas propriedades do arquivo.

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

- Toda mudança é gravada de forma segura: o complemento escreve um arquivo temporário e só então troca pelo arquivo antigo, que fica guardado como cópia de segurança `NotasWorkflowNVDA-data.json.bak`.
- A gravação acontece em segundo plano, meio segundo depois da última mudança, para o NVDA nunca parar de responder; várias mudanças seguidas viram uma gravação só. Ao encerrar o NVDA, tudo o que estiver pendente é gravado antes.
- Se o arquivo estiver danificado, ele é guardado com outro nome (`NotasWorkflowNVDA-data.corrupt-` seguido da data) e a cópia de segurança é usada. O NVDA avisa. Nenhum arquivo é apagado.
- Se não for possível gravar (disco cheio, pasta sem permissão), as folhas continuam abertas, o NVDA avisa e a próxima mudança tenta de novo.

### Muitas folhas

O complemento foi medido com 100 mil folhas. O NVDA inicia na hora: as folhas são lidas em segundo plano em poucos segundos, e se você usar um comando antes disso o NVDA fala "Carregando as folhas…" e espera terminar. Mudar o status, abrir uma folha, salvar e buscar levam frações de segundo. O arquivo pode ter até 200 MB (cerca de 300 mil folhas como as de um uso comum).

### Usar em mais de um computador

Escolha como pasta das folhas uma pasta do **OneDrive** ou do **Google Drive para computador**. Esses programas sincronizam o arquivo sozinhos. Ao abrir a janela Notas Workflow NVDA, o complemento percebe se o arquivo foi mudado em outro computador e lê as folhas de novo.

> **Atenção:** se dois computadores mudarem as folhas ao mesmo tempo, vale a última gravação. A cópia de segurança `.bak` guarda a versão anterior.

## Importar e exportar

### Exportar

**Exportar folhas… (Alt+E)** nas configurações grava todas as folhas, cadernos e pastas num arquivo `.json`. O NVDA fala "Exportado:" e o número de folhas. O arquivo serve como cópia de segurança e para levar as folhas para outro computador. Para ter as folhas num documento para ler ou enviar, use o botão **Exportar…** da janela principal (veja Exportar como documento); esses documentos não podem ser importados de volta.

### Importar

**Importar folhas… (Alt+I)** junta as folhas de um arquivo exportado às suas:

- folhas, cadernos e pastas novos são acrescentados;
- quando o arquivo traz uma folha que você já tem (mesmo identificador), fica a versão alterada por último;
- dados inválidos são corrigidos ou descartados, e arquivos acima de 200 MB não são abertos.

O NVDA fala "Importado:" com o número de folhas, cadernos e pastas trazidos.

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
| Enter | Lista de folhas, Organização, resultados | Abrir a folha |
| Delete | Lista de folhas, Organização | Excluir |
| Alt+Shift+Seta para a direita | Lista de folhas | Status seguinte |
| Alt+Shift+Seta para a esquerda | Lista de folhas | Status anterior |
| F2 | Organização | Renomear (ou mudar o título de uma folha) |
| Ctrl+S | Janela da folha | Salvar agora |
| Ctrl+B | Conteúdo | Negrito |
| Ctrl+I | Conteúdo | Itálico |
| Esc | Qualquer janela | Fechar (na janela da folha, salva antes) |

## Mensagens faladas

| O NVDA fala | Quando |
|---|---|
| Folha criada em A fazer | Uma folha foi criada (com o nome do status escolhido). |
| Status atualizado para Em andamento | O status da folha mudou. |
| Já está na primeira raia / Já está na última raia | Não há status anterior ou seguinte. |
| Agora em: Caderno Trabalho | A folha (ou o caderno) foi movida para outro lugar. |
| Folha excluída: título | A folha foi excluída. |
| Folha salva | Ctrl+S, ou o salvamento automático com o anúncio ligado. |
| Negrito, Lista numerada… / Negrito removido | Um formato foi aplicado ou removido. |
| Encontrado: 3 folhas / Nenhuma folha encontrada | Resultado da busca. |
| Caderno … criado, Pasta … criada, Renomeado para …, … excluído | Criar, renomear e excluir cadernos, pastas e folhas. |
| Carregando as folhas… | Um comando foi usado logo depois de o NVDA iniciar, enquanto as folhas ainda eram lidas. |
| Importado: … / Exportado: … | Importação e exportação. |
| Exportado: 3 folhas, em Trabalho.docx | Exportar… gravou o documento. |
| Exportado: 3 folhas, um arquivo por folha, na pasta … | Exportar… gravou um arquivo para cada folha. |
| Nada para exportar: Caderno … não tem folhas. | O caderno ou a pasta escolhida está vazia. |
| Não há cadernos. / Não há pastas. | Exportar… > Caderno… ou Pasta… sem nenhum caderno ou pasta. |
| Não foi possível exportar para … | O documento exportado não pôde ser gravado: confira a pasta. |
| Folhas salvas na nova pasta / Usando as folhas da nova pasta | A pasta das folhas mudou. |
| Folhas da versão anterior trazidas para o Notas Workflow NVDA: 2 folhas… | Primeiro início depois de trocar o NotasWorkflow 1.0.0 pelo Notas Workflow NVDA. |
| Esta folha foi excluída. | A folha aberta foi excluída por outro caminho; nada é recriado. |
| As folhas salvas estavam danificadas… | O arquivo estava danificado; foi guardado com outro nome. |
| Não foi possível salvar as folhas em … | Erro de gravação: confira a pasta. |
| Este arquivo não tem folhas do Notas Workflow NVDA. | O arquivo escolhido para importar não é válido. |
| O arquivo tem mais de 200 MB e não foi aberto. | Arquivo grande demais. |
| O nome não pode ficar vazio. | Caderno ou pasta sem nome. |

## Privacidade e segurança

- O complemento **não usa a internet**: nenhuma folha sai do computador, e não há conta nem senha.
- O título, o conteúdo e as tags das folhas **nunca** vão para o log do NVDA.
- Excluir sempre pede confirmação, com Não como padrão; excluir caderno ou pasta nunca apaga folhas.
- Arquivos importados são conferidos: tamanhos, tipos e identificadores inválidos são corrigidos ou descartados, e o conteúdo nunca é exibido como página nem executado.
- O complemento fica desligado nas telas seguras do Windows (tela de logon e controle de conta de usuário).
- As folhas ficam num arquivo de texto legível na pasta do seu perfil do Windows.
- Os documentos exportados levam só o que está nas folhas e na formatação do editor: scripts, estilos, links e imagens que viessem de um arquivo importado são descartados, e a página HTML não carrega nada da internet.

## Perguntas frequentes

### O NVDA diz que não foi possível salvar as folhas

A pasta das folhas não existe mais ou não pode ser gravada (por exemplo, um pen drive removido). Escolha outra pasta nas configurações ou use **Usar a pasta padrão**. As folhas abertas continuam na memória até lá.

### Minhas folhas sumiram depois de trocar a pasta

A pasta nova já tinha folhas do Notas Workflow NVDA, e elas passaram a ser usadas. Volte à pasta anterior nas configurações: as folhas antigas continuam lá.

### O arquivo estava danificado

O complemento guardou o arquivo danificado com o nome `NotasWorkflowNVDA-data.corrupt-` seguido da data e usou a cópia de segurança. Se quiser, envie o arquivo guardado para análise; ele nunca é apagado.

### Não encontro uma folha numa raia com muitas folhas

Cada raia mostra 200 folhas por vez. Use "Mostrar mais" no fim da raia, a caixa Mostrar para ver só um caderno ou uma pasta, ou a busca (NVDA+Alt+B), que encontra a folha na hora e a mostra selecionada ao voltar.

### Escrevi um asterisco e ele sumiu

Pares de asteriscos em volta de uma palavra viram itálico (`*palavra*`). Para mostrar asteriscos, use-os no meio de palavras ou números, como `2*3`.

## Histórico deste manual

| Versão | Mudanças |
|---|---|
| 1.0.0 | Primeira versão do manual, com todas as funcionalidades da versão 1.0.0 do complemento. |
| 1.1.0 | Novo nome do complemento, Notas Workflow NVDA, com os novos nomes de pasta e arquivo; nova seção "Quem usava o NotasWorkflow 1.0.0" com a migração das folhas; nova mensagem falada da migração. |
| 1.3.0 | As raias começam fechadas e ficam como você as deixou; ao mudar o status ou o local na janela da folha, o foco vai para a próxima folha da mesma raia (nova seção "Trabalhar a pilha de uma raia"). |
| 1.2.0 | Botão Criar (folha, caderno e pasta); Atualizar o status da tarefa; Mover para (caderno ou pasta, e folhas guardadas direto em pastas); Enter abre a folha; sem a visualização em tabela e sem o botão Abrir; folhas listadas e abertas na janela Cadernos e pastas; campo Local; listas de 200 em 200; desempenho com 100 mil folhas; sem menções a outras plataformas. |
| 1.4.0 | Novo botão Exportar… na janela principal e novo capítulo "Exportar como documento": folha selecionada, caderno ou pasta em Word, Markdown ou HTML, num arquivo só ou num arquivo para cada folha; novas mensagens faladas da exportação. |
