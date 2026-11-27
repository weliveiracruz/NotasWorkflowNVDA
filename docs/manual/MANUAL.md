# Notas Workflow NVDA

## Sobre este manual

Este é o manual de uso do complemento **Notas Workflow NVDA**, versão {{versao}}, para o leitor de telas NVDA. Ele descreve o complemento como ele é hoje: todas as janelas, campos, botões, teclas e mensagens faladas.

O Notas Workflow NVDA organiza **folhas** (anotações e tarefas) em **raias** de status, agrupadas em **cadernos** e **pastas**. As folhas têm conteúdo com formatação, são salvas sozinhas e podem ser buscadas e exportadas como documentos. Tudo funciona pelo teclado, com respostas faladas, e continua rápido mesmo com dezenas de milhares de folhas.

### Como abrir este manual

O manual vem dentro do complemento e abre na janela de leitura do NVDA:

- no menu do NVDA, **Preferências, Configurações**, categoria **Notas Workflow NVDA**, botão **Manual de uso… (Alt+N)**;
- ou pelo comando "abre o manual de uso", que não tem atalho padrão: dê um atalho a ele em **Preferências, Definir comandos**, categoria Notas Workflow NVDA.

Na janela de leitura, navegue como numa página: **H** passa pelos títulos, **2** pelos capítulos, **3** pelas seções, **T** pelas tabelas e **K** pelos links do sumário. **Esc** fecha o manual.

> **Dica:** os nomes de botões e campos deste manual são os da interface em português. Entre parênteses aparece a tecla de atalho de cada um, por exemplo **Criar… (Alt+C)**.

## Novidades da versão {{versao}}

- **Ordem das pastas e dos cadernos**: com as mesmas teclas que mudam a ordem das folhas, **Ctrl+Shift+Seta para cima** e **Ctrl+Shift+Seta para baixo**, você sobe ou desce uma pasta ou um caderno no campo **Mostrar** da janela principal e na árvore **Organização** de Cadernos e pastas. A nova ordem vale em todas as listas (veja "Mudar a ordem das pastas e dos cadernos").
- **Manual de uso nas configurações**: o botão **Manual de uso…** saiu da janela principal e agora fica nas configurações do complemento (veja "Como abrir este manual").
- **Manual reescrito**: este manual foi reorganizado por tarefa e descreve só o complemento como ele é hoje, sem o histórico das versões. As mudanças de cada versão continuam na ajuda do complemento, na Loja de complementos do NVDA.

## Conceitos

### Folha

Uma folha é uma anotação ou uma tarefa. Ela tem:

- um **título** (obrigatório, até 200 caracteres);
- o **conteúdo**, um texto de várias linhas com formatação (até 1 MB);
- um **status**, que é a raia em que ela está;
- um **local**: um caderno, uma pasta ou nenhum;
- a data de criação e a data da última alteração.

A folha que não está em nenhum caderno nem em nenhuma pasta é uma **folha solta**.

### Raias (status)

As raias são os status das tarefas, sempre nesta ordem:

| Raia | Uso sugerido |
|---|---|
| A fazer | O que ainda vai começar. É o status de uma folha nova, se você não escolher outro. |
| Em andamento | O que está sendo feito agora. |
| Bloqueada | O que está parado, esperando alguma coisa. |
| Concluída | O que terminou. |

O NVDA sempre diz a raia pelo **nome**: nenhuma informação depende de cor.

### Cadernos e pastas

Um **caderno** agrupa folhas, por exemplo "Trabalho" ou "Faculdade". Uma **pasta** agrupa cadernos e também pode guardar folhas diretamente, por exemplo a pasta "Projetos" com os cadernos "Site" e "Aplicativo" e algumas folhas gerais.

- Uma folha fica num lugar só: num caderno, direto numa pasta ou solta.
- Um caderno fica em no máximo uma pasta, ou sem pasta.
- Nomes de cadernos e pastas têm até 100 caracteres e não podem ficar vazios.
- Pastas, cadernos e folhas têm uma **ordem**, que você muda pelo teclado e que é a mesma em todas as listas.

## Instalação e requisitos

- NVDA 2024.1 ou mais novo (testado até o NVDA 2026.1.1).
- Windows 10 ou 11.
- Não precisa de internet, de conta nem de navegador.

Para instalar, abra o arquivo `NotasWorkflowNVDA-{{versao}}.nvda-addon` com o NVDA em execução, confirme a instalação e reinicie o NVDA quando ele pedir.

Para desinstalar, use o menu do NVDA, **Ferramentas, Loja de complementos**, aba Complementos instalados. **Desinstalar não apaga as suas folhas**: elas continuam na pasta das folhas (veja "Onde ficam as folhas").

### Quem usava o antigo NotasWorkflow

O complemento já se chamou **NotasWorkflow**. O Notas Workflow NVDA é tratado pelo NVDA como outro complemento, e no primeiro início ele **copia** uma única vez as folhas da pasta antiga (`%APPDATA%\nvda\NotasWorkflow`) e as configurações (pasta das folhas, salvamento automático e anúncio). O NVDA fala "Folhas da versão anterior trazidas para o Notas Workflow NVDA" e o número de folhas.

O arquivo antigo `NotasWorkflow-data.json` nunca é alterado nem apagado. Se você usava uma pasta das folhas própria (por exemplo, no OneDrive), ela continua em uso, e o arquivo antigo é copiado para o nome novo `NotasWorkflowNVDA-data.json`. Depois de conferir as folhas com **NVDA+Alt+N**, desinstale o NotasWorkflow antigo e reinicie o NVDA: enquanto os dois estiverem instalados, os atalhos NVDA+Alt+N, NVDA+Alt+F e NVDA+Alt+B ficam repetidos.

## Primeiros passos

1. Pressione **NVDA+Alt+N** para abrir a janela Notas Workflow NVDA. O foco fica na lista de folhas, na primeira raia.
2. Pressione **Alt+C** (botão Criar…) e escolha **Folha…** no menu. Digite o título e pressione **Enter**. O NVDA fala "Folha criada em A fazer".
3. A janela da folha abre com o foco no **Conteúdo**. Escreva o que quiser: a folha é salva sozinha 2 segundos depois que você para de digitar.
4. Pressione **Esc** para salvar e voltar para a lista. A folha nova está selecionada.
5. Pressione **Alt+Shift+Seta para a direita** para mudar o status para Em andamento. O NVDA fala "Status atualizado para Em andamento".
6. Pressione **Ctrl+Shift+Seta para cima** para subir a folha na raia, e **Enter** para abri-la de novo.

## Janela Notas Workflow NVDA

Abra com **NVDA+Alt+N** de qualquer lugar, ou pelo item **Notas Workflow NVDA…** do menu Ferramentas do NVDA. A janela é única: abrir de novo traz a mesma janela para a frente, na mesma folha. Fechar só esconde a janela, então reabrir é instantâneo. Se o arquivo das folhas foi mudado em outro computador (pasta sincronizada), as folhas são lidas de novo ao abrir.

### Controles da janela

Os controles aparecem nesta ordem de tabulação:

| Controle | Atalho | O que faz |
|---|---|---|
| Mostrar | Alt+O | Árvore que escolhe quais folhas aparecem, com as pastas e os cadernos (veja "O campo Mostrar"). |
| Folhas | Alt+F | A lista de folhas em raias. O rótulo diz o que está sendo mostrado e quantas folhas há, por exemplo "Folhas: Caderno: Trabalho (4)". |
| Criar… | Alt+C | Menu para criar uma folha, um caderno, uma pasta ou uma folha a partir de documento (veja "Criar folhas, cadernos e pastas"). |
| Buscar… | Alt+B | Abre a janela Buscar folhas. |
| Cadernos e pastas… | Alt+T | Abre a janela Cadernos e pastas, que organiza os lugares e também lista e abre as folhas. |
| Exportar… | Alt+E | Grava a folha selecionada, um caderno ou uma pasta como documento do Word, Markdown ou HTML (veja "Exportar como documento"). |
| Fechar | Alt+H ou Esc | Fecha (esconde) a janela. |

A janela não tem botões para mudar o status, mover ou excluir a folha: isso é feito pelas teclas da lista de folhas e pelos campos da janela da folha.

### O campo Mostrar

O campo **Mostrar (Alt+O)** é uma árvore com, nesta ordem:

| Opção | Mostra |
|---|---|
| Todas as folhas | Todas as folhas. |
| Folhas soltas | As folhas que não estão em nenhum caderno nem em nenhuma pasta. |
| Folhas recentes | As 10 folhas alteradas por último, da mais recente para a mais antiga. |
| Pasta: nome | As folhas guardadas direto na pasta e as dos cadernos dela. Há uma opção para cada pasta, com os cadernos dela dentro. |
| Caderno: nome | As folhas daquele caderno. Os cadernos de uma pasta ficam dentro dela; os cadernos sem pasta vêm no fim. |

As pastas começam fechadas; só abre a pasta do caderno que está sendo mostrado. Selecionar uma opção já mostra as folhas dela na lista.

| Tecla | Ação |
|---|---|
| Seta para cima e Seta para baixo | Passam pelas opções; as folhas da opção selecionada aparecem na hora. |
| Seta para a direita | Abre a pasta selecionada, mostrando os cadernos dela. |
| Seta para a esquerda | Fecha a pasta, ou volta de um caderno para a pasta dele. |
| Enter | Vai para a lista de folhas. |
| Ctrl+Shift+Seta para cima | Sobe a pasta ou o caderno selecionado uma posição. |
| Ctrl+Shift+Seta para baixo | Desce a pasta ou o caderno selecionado uma posição. |

### A lista de folhas

A lista **Folhas (Alt+F)** é uma árvore com uma raia por ramo, por exemplo "A fazer, 3 folhas". As raias **começam fechadas**: **Seta para a direita** abre uma raia e **Seta para a esquerda** fecha. Enquanto a janela estiver aberta, as raias ficam como você as deixou, e a raia de uma folha selecionada pelo complemento (ao criar uma folha, ao voltar da busca, ao mudar o status) abre sozinha.

Dentro da raia, cada folha é lida com o título, o local (quando existe) e a data, por exemplo:

`Relatório mensal, caderno Trabalho, atualizada em 12/10/2026`

Cada raia mostra **200 folhas por vez**. Quando há mais, o último item da raia é "Mostrar mais 200 folhas (N ainda não mostradas)": **Enter** nele mostra as próximas, com o foco na primeira delas. Uma folha aberta pela busca ou escolhida em outro lugar sempre aparece, mesmo além das primeiras 200.

| Tecla | Ação |
|---|---|
| Enter | Abre a folha selecionada. Numa raia, abre ou fecha a raia; em "Mostrar mais", mostra as próximas folhas. |
| Delete | Exclui a folha selecionada, depois de confirmar. |
| Alt+Shift+Seta para a direita | Muda o status da folha para o seguinte. |
| Alt+Shift+Seta para a esquerda | Muda o status da folha para o anterior. |
| Ctrl+Shift+Seta para cima | Sobe a folha uma posição na raia. |
| Ctrl+Shift+Seta para baixo | Desce a folha uma posição na raia. |

## Criar folhas, cadernos e pastas

O botão **Criar… (Alt+C)**, na janela principal e em Cadernos e pastas, abre um menu:

| Opção | O que acontece |
|---|---|
| Folha… | Abre a janela Nova folha. A folha começa no status selecionado na lista e no caderno ou na pasta em uso. |
| Caderno… | Abre a janela Novo caderno, com o nome e a pasta. |
| Pasta… | Pergunta o nome da pasta. O NVDA fala "Pasta … criada". |
| Folha a partir de documento… | Cria uma folha com o texto de um documento (veja "Folha a partir de documento"). |

De qualquer lugar, **NVDA+Alt+F** abre a janela Nova folha.

### Janela Nova folha

| Campo | Atalho | Descrição |
|---|---|---|
| Título | Alt+T | Obrigatório, até 200 caracteres. |
| Local | Alt+O | Árvore com Folha solta, as pastas e os cadernos (veja "O campo Local"). |
| Novo caderno… | Alt+C | Abre a janela Novo caderno já com a pasta do item escolhido em Local. O caderno criado aparece em Local, já escolhido, com o foco nele. |
| Nova pasta… | Alt+P | Pergunta o nome da pasta. A pasta criada aparece em Local, já escolhida, com o foco nela. |
| Status | Alt+S | A fazer, Em andamento, Bloqueada ou Concluída. |
| Criar | Alt+R ou Enter | Cria a folha. Fica indisponível enquanto o título estiver vazio. Enter na árvore Local também cria. |
| Cancelar | Esc | Fecha sem criar a folha. |

Com Novo caderno… e Nova pasta… você cria o lugar da folha sem sair da janela: o título digitado continua lá. Para um caderno dentro de uma pasta nova, crie primeiro a pasta e depois o caderno. Se você cancelar a Nova folha, o caderno e a pasta criados continuam existindo. Cancelar o nome não cria nada e o foco volta para o botão.

Ao criar, o NVDA fala "Folha criada em" e o status, e a janela da folha abre com o foco no Conteúdo.

### Janela Novo caderno

| Campo | Atalho | Descrição |
|---|---|---|
| Nome | Alt+N | Obrigatório, até 100 caracteres. |
| Pasta | Alt+P | **Nenhuma pasta** ou uma das pastas. Vem escolhida a pasta em uso (a mostrada no campo Mostrar, ou a selecionada em Cadernos e pastas). |
| Nova pasta… | Alt+V | Pergunta o nome de uma pasta nova, que entra na lista Pasta já escolhida, com o foco nela. O nome do caderno continua lá. |
| Criar | Alt+R ou Enter | Cria o caderno. Fica indisponível enquanto o nome estiver vazio. O NVDA fala "Caderno … criado". |
| Cancelar | Esc | Fecha sem criar nada. |

### O campo Local

O campo **Local (Alt+O)** aparece na janela Nova folha, na janela da folha e em Mover para…. É uma árvore que funciona como as raias: as pastas começam **fechadas**, dizem quantos cadernos têm e guardam os cadernos **dentro** delas.

| Item | Onde a folha fica |
|---|---|
| Folha solta (sem caderno nem pasta) | Em nenhum caderno e em nenhuma pasta. |
| Pasta Projetos, 2 cadernos | Direto na pasta, sem caderno. |
| Caderno Site (dentro da pasta Projetos) | No caderno, que está na pasta. |
| Caderno Casa (no fim, fora das pastas) | No caderno sem pasta. |

- **Seta para cima e Seta para baixo** passam pelos itens; **Seta para a direita** abre a pasta e **Seta para a esquerda** fecha (ou volta do caderno para a pasta).
- O item selecionado é o local: a própria pasta guarda a folha direto nela; um caderno guarda a folha no caderno.
- A árvore começa no local atual da folha (numa folha nova, no caderno ou na pasta em uso), com só a pasta dele aberta.

### Folha a partir de documento

**Criar… > Folha a partir de documento…** (ou o comando sem atalho padrão em Definir comandos) traz o texto de um documento para uma folha nova:

1. Escolha o arquivo na janela do Windows.
2. O NVDA fala "Lendo o documento…". A leitura acontece em segundo plano, então o NVDA continua respondendo.
3. A janela Nova folha abre com o título preenchido: o título do documento, o assunto do e-mail ou, se não houver, o nome do arquivo.
4. Ao criar, o NVDA fala "Folha criada em", o status e o nome do arquivo, e a janela da folha abre com o texto no Conteúdo.

| Documento | O que vem para a folha |
|---|---|
| Word (.docx) | Os parágrafos, com títulos (estilos Título e Título 1 a 6), listas com marcadores e numeradas, **negrito**, itálico e tachado. |
| PowerPoint (.pptx) | Cada slide vira o título "Slide 1: título do slide", com os textos e os marcadores; as anotações do orador vêm depois de "Anotações do orador:", como citação. |
| Texto (.txt) | As linhas do arquivo (UTF-8, UTF-16 ou a codificação padrão do Windows); linhas que começam com • viram itens de lista. |
| Página HTML (.html, .htm) | O texto da página, com títulos, listas, negrito e itálico; scripts, estilos, imagens e links ficam de fora. |
| E-mail (.eml) | As linhas **De:**, **Para:**, **Cc:**, **Data:** e **Anexos:** (só os nomes dos arquivos), um divisor e o corpo da mensagem. |

- As tabelas viram uma linha por linha da tabela, com as células separadas por " | ". Imagens e linhas em branco não vêm.
- Uma folha guarda até 1 MB: de um documento maior, só a primeira parte vem, com aviso. Documentos acima de 50 MB não são lidos.
- Não são lidos: .doc, .ppt, .rtf, PDF e mensagens do Outlook (.msg). Para uma mensagem do Outlook, salve-a como HTML ou texto no Outlook, ou copie o texto e cole no Conteúdo.
- Um documento danificado, protegido por senha ou sem texto não é lido, e o NVDA avisa.

## Janela da folha

Abre com **Enter** sobre uma folha (na lista de folhas, nos resultados da busca ou em Cadernos e pastas) e logo depois de criar uma folha. O título da janela é o título da folha.

### Campos

| Campo | Atalho | Descrição |
|---|---|---|
| Título | Alt+T | O título da folha. Uma folha sem título aparece como "Sem título". |
| Local | Alt+O | Muda o caderno ou a pasta da folha (veja "O campo Local"). |
| Status | Alt+S | Muda o status da folha. |
| Conteúdo | Alt+C | O texto da folha, com várias linhas e a marcação de formatação. |
| Formatação… | Alt+F | Abre o menu de formatos (veja "Formatação do conteúdo"). |
| Inserir documento… | Alt+D | Coloca o texto de um documento no Conteúdo, na posição do cursor. |
| Situação do salvamento | Alt+I | Campo somente leitura que diz se tudo está salvo. |
| Salvar e fechar | Alt+L | Salva o que estiver pendente e fecha. **Esc** faz o mesmo. |

### Salvamento automático

Ao digitar, a Situação do salvamento passa a "Alterações não salvas…". Dois segundos depois da última mudança (o tempo é ajustável nas configurações), a folha é salva.

| Situação | Significado |
|---|---|
| Salva | Nada mudou desde que a janela abriu. |
| Alterações não salvas… | Há mudanças esperando o salvamento automático. |
| Salva às 14:32 | Tudo salvo, por último naquele horário. |
| Não salva | A gravação falhou; a próxima mudança tenta de novo. |

**Nada se perde:** **Ctrl+S** salva na hora (o NVDA fala "Folha salva"), e fechar a janela por Esc, por Salvar e fechar ou pelo botão de fechar sempre salva o que estiver pendente, até se o NVDA for encerrado com a janela aberta. Só os campos que você mudou são gravados.

### Inserir documento

O botão **Inserir documento… (Alt+D)** coloca o texto de um documento numa folha que já existe:

1. Deixe o cursor do Conteúdo onde o texto deve entrar (ou selecione o trecho que ele vai substituir).
2. Pressione **Alt+D** e escolha o arquivo. O NVDA fala "Lendo o documento…".
3. O texto entra em linhas próprias, nunca no meio de uma linha, e o cursor vai para o fim dele. O NVDA fala "Texto de", o nome do arquivo, e "inserido".

Os documentos aceitos são os mesmos de "Folha a partir de documento". Se a folha já estiver cheia (1 MB), nada é inserido; se só parte couber, entra a primeira parte, com aviso.

## Formatação do conteúdo

O conteúdo é texto com uma marcação leve, fácil de ler com o NVDA. O complemento guarda o texto formatado e o mostra de volta do mesmo jeito, sem perder nada.

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

O botão **Formatação… (Alt+F)** abre um menu com Negrito (Ctrl+B), Itálico (Ctrl+I), Tachado, Código, Título 2, Título 3, Lista com marcadores, Lista numerada, Citação e Divisor.

- Negrito, Itálico, Tachado e Código valem para o **texto selecionado**. Sem seleção, as marcas são inseridas e o cursor fica entre elas.
- Título 2, Título 3, as listas e a Citação valem para a **linha atual** ou para as linhas selecionadas. A Lista numerada numera as linhas em sequência.
- Divisor insere uma linha `---` própria na posição do cursor.
- Escolher de novo um formato já aplicado o **remove**: o NVDA fala, por exemplo, "Negrito removido".
- No Conteúdo, **Ctrl+B** e **Ctrl+I** aplicam negrito e itálico sem abrir o menu.

Exemplo: as linhas `## Reunião de segunda`, `- revisar o **orçamento**` e `- marcar *demo* com o cliente` viram um título seguido de uma lista com dois itens, com "orçamento" em negrito e "demo" em itálico.

## Organizar as folhas

### Mudar o status

- Na lista de folhas, **Alt+Shift+Seta para a direita** passa a folha para o status seguinte e **Alt+Shift+Seta para a esquerda** para o anterior. O NVDA fala "Status atualizado para" e o nome do status, e a seleção acompanha a folha. Nas pontas, o NVDA diz "Já está na primeira raia" ou "Já está na última raia".
- Na janela da folha, escolha outro item no campo **Status**.

### Trabalhar a pilha de uma raia

Quando você muda o status ou o local de uma folha **na janela da folha**, ao fechar a janela o foco não acompanha a folha: ele vai para a **próxima folha da mesma raia**. Assim dá para tratar uma raia em sequência: Enter na primeira folha, mudar o status, Esc, e o foco já está na seguinte.

- Se a folha era a última da raia, o foco vai para a anterior; se era a única, para a própria raia.
- Se você só editou a folha, sem mudar o status nem tirá-la do que está sendo mostrado, o foco volta para ela.

### Mudar a ordem das folhas na raia

Selecione a folha na lista e pressione **Ctrl+Shift+Seta para cima** para subir uma posição ou **Ctrl+Shift+Seta para baixo** para descer. A seleção acompanha a folha e o NVDA diz a nova posição, por exemplo "Posição 2 de 5". A ordem é salva na hora e a data de alteração da folha não muda.

- Nas pontas, o NVDA diz "Já está no topo da raia" ou "Já está no fim da raia".
- Com um caderno ou uma pasta no campo Mostrar, a folha passa a vizinha que aparece; as folhas de outros lugares ficam onde estão. A ordem é a mesma em todos os filtros.
- Em **Folhas recentes** a ordem é sempre a da última alteração, e o NVDA avisa que ali ela não pode ser mudada.
- Numa raia longa, a última folha de uma página pode descer para a página seguinte, que aparece.

### Mudar a ordem das pastas e dos cadernos

As pastas e os cadernos mudam de ordem com **as mesmas teclas das folhas**, no campo **Mostrar** da janela principal e na árvore **Organização** de Cadernos e pastas. Selecione a pasta ou o caderno e pressione **Ctrl+Shift+Seta para cima** (sobe uma posição) ou **Ctrl+Shift+Seta para baixo** (desce uma posição).

- Uma **pasta** muda de lugar entre as pastas.
- Um **caderno** muda de lugar entre os cadernos da mesma pasta, ou entre os cadernos sem pasta: ele nunca sai da pasta por essas teclas. Para levá-lo a outra pasta, use **Mover para…** em Cadernos e pastas.
- A seleção acompanha o item, as pastas abertas continuam abertas e o NVDA diz a nova posição, por exemplo "Posição 2 de 3". No campo Mostrar, as folhas mostradas não mudam.
- Nas pontas, o NVDA diz "Já está no topo da lista" ou "Já está no fim da lista".
- Em Todas as folhas, Folhas soltas, Folhas recentes, Sem pasta, Folhas soltas da Organização ou numa folha, o NVDA diz "Aqui só pastas e cadernos mudam de ordem" e nada muda.

A nova ordem é salva na hora e vale em todas as listas: Mostrar, Local, Mover para, Organização e os documentos exportados.

### Mover para um caderno ou uma pasta

- Na janela da folha, escolha outro item no campo **Local**.
- Em Cadernos e pastas, selecione a folha e use **Mover para… (Alt+M)**. A janela "Mover … para" (com o título da folha) tem a árvore Local, começando no lugar atual. **Enter** ou **OK** move; **Cancelar** ou **Esc** deixa a folha onde estava.

O NVDA confirma com "Agora em:" e o lugar, com a pasta do caderno, por exemplo "Agora em: Caderno Site (pasta Projetos)".

### Excluir uma folha

Na lista de folhas ou na árvore Organização, **Delete** pergunta "Excluir a folha …? Isso não pode ser desfeito.", com **Não** como resposta padrão. Ao confirmar, o NVDA fala "Folha excluída:" e o título, e a seleção vai para a folha vizinha.

## Buscar folhas

Use **NVDA+Alt+B** de qualquer lugar, ou **Buscar… (Alt+B)** na janela principal.

| Controle | Atalho | Descrição |
|---|---|---|
| Buscar | Alt+B | Digite as palavras. A busca roda sozinha logo depois que você para de digitar; Enter busca na hora e leva o foco aos resultados. |
| Resultados | Alt+R | Tabela com Título, Trecho, Relevância e Atualizada em. O rótulo diz quantos resultados há. Enter abre a folha. |
| Abrir | Alt+A | Abre a folha selecionada nos resultados. |
| Fechar | Alt+H ou Esc | Fecha a busca. |

- Procura no título e no conteúdo, sem diferenciar acentos nem maiúsculas: "acao" encontra "Ação".
- A **relevância** é a porcentagem das palavras buscadas que a folha contém; no empate, vêm primeiro as que têm as palavras no título e depois as alteradas por último.
- O **trecho** mostra até 120 caracteres em volta da primeira palavra encontrada. Aparecem no máximo 100 resultados.
- O NVDA fala "Encontrado:" e o número de folhas, ou "Nenhuma folha encontrada".
- Ao voltar de uma folha aberta pela busca, os resultados são atualizados e a folha continua selecionada.

## Cadernos e pastas

Abra pelo botão **Cadernos e pastas… (Alt+T)** da janela principal.

### A árvore Organização

A árvore **Organização (Alt+O)** mostra tudo:

- cada pasta, por exemplo "Pasta Projetos, 2 cadernos, 3 folhas", com os cadernos dela e depois as folhas guardadas direto nela;
- cada caderno, por exemplo "Trabalho, 4 folhas", com as folhas dele;
- o ramo "Sem pasta", com os cadernos que não estão em nenhuma pasta;
- o ramo "Folhas soltas".

Cada folha é lida com o título, o status e a data. As folhas só são carregadas quando você abre o ramo, 200 por vez, com "Mostrar mais" no fim.

| Tecla | Ação |
|---|---|
| Enter | Abre a folha; num ramo, abre ou fecha o ramo. |
| F2 | Renomeia a pasta ou o caderno; numa folha, muda o título. |
| Delete | Exclui a pasta, o caderno ou a folha, depois de confirmar. |
| Ctrl+Shift+Seta para cima | Sobe a pasta ou o caderno uma posição. |
| Ctrl+Shift+Seta para baixo | Desce a pasta ou o caderno uma posição. |

### Botões

| Botão | Atalho | O que faz |
|---|---|---|
| Criar… | Alt+C | Menu com Folha…, Caderno…, Pasta… e Folha a partir de documento…. A folha nasce no caderno ou na pasta selecionada; no Novo caderno, a pasta selecionada já vem escolhida. |
| Renomear… | Alt+R ou F2 | Renomeia a pasta ou o caderno; numa folha, muda o título. O NVDA fala "Renomeado para" e o nome. |
| Mover para… | Alt+M | Numa folha, move para um caderno, uma pasta ou a deixa solta; num caderno, move para outra pasta ou para Sem pasta. |
| Excluir | Alt+X ou Delete | Exclui a pasta, o caderno ou a folha selecionada, depois de confirmar. |
| Fechar | Alt+H ou Esc | Fecha a janela. |

### Excluir pastas e cadernos

Excluir uma pasta ou um caderno **exclui tudo o que está dentro**:

- ao excluir um **caderno**, as folhas dele também são excluídas;
- ao excluir uma **pasta**, são excluídos os cadernos dela, as folhas desses cadernos e as folhas guardadas direto na pasta.

Antes, o NVDA pergunta dizendo quanto será excluído, por exemplo "Excluir a pasta Projetos e tudo o que está nela: 2 cadernos e 5 folhas? Isso não pode ser desfeito.", com **Não** como padrão. As folhas de outros lugares não mudam. Para guardar alguma folha, mova-a antes de excluir.

## Exportar como documento

O botão **Exportar… (Alt+E)** da janela principal grava folhas como documentos para ler, imprimir ou enviar. É diferente de **Exportar folhas…** das configurações, que grava a cópia de segurança `.json`.

### O que exportar

| Opção | O que exporta |
|---|---|
| Folha selecionada… | A folha selecionada na lista. Só aparece com uma folha selecionada. |
| Caderno… | Todas as folhas de um caderno. A lista "Exportar qual caderno?" começa no caderno mostrado ou no da folha selecionada. |
| Pasta… | As folhas guardadas direto na pasta e as dos cadernos dela. A lista "Exportar qual pasta?" começa na pasta mostrada ou na da folha selecionada. |

Sem cadernos (ou pastas), o NVDA fala "Não há cadernos." (ou "Não há pastas."). Um caderno ou uma pasta sem folhas não é exportado: o NVDA fala "Nada para exportar:" e o nome.

### Formato e arquivos

| Formato | Bom para |
|---|---|
| Documento do Word (.docx) | Abrir no Word, no LibreOffice ou no Google Docs, imprimir e enviar. |
| Markdown (.md) | Texto simples com marcação, para outros programas de anotações. |
| Página HTML (.html) | Abrir no navegador, sem nenhum programa a mais. |

Num caderno ou numa pasta, escolha também como gravar:

- **Um arquivo com todas as folhas**: a janela do Windows pergunta o nome e o lugar, já com o nome do caderno ou da pasta; se o arquivo existe, o Windows pergunta antes de substituir.
- **Um arquivo para cada folha**: a janela do Windows pergunta a pasta. O complemento cria nela uma pasta nova com o nome do caderno ou da pasta, com um arquivo por folha (e uma subpasta por caderno, numa pasta). **Nada é sobrescrito**: "Trabalho (2)" se "Trabalho" já existe; "Título (2).md" para títulos repetidos. Caracteres que o Windows não aceita saem dos nomes.

A gravação acontece em segundo plano. Ao terminar, o NVDA fala, por exemplo, "Exportado: 3 folhas, em Trabalho.docx" ou "Exportado: 12 folhas, um arquivo por folha, na pasta" e o caminho; se falhar, "Não foi possível exportar para" e o caminho.

### Como fica o documento

- Um caderno num arquivo só começa com o título 1 "Caderno" e o nome, com a data da exportação e o número de folhas; cada folha é um título 2.
- Uma pasta começa com o título 1 "Pasta" e o nome; as folhas direto nela ficam sob o título 2 "Folhas direto na pasta" e as de cada caderno sob o título 2 com o nome do caderno; cada folha é um título 3.
- Uma folha sozinha (ou cada arquivo de "um arquivo para cada folha") tem o título da folha como título 1.
- As folhas vêm na ordem das raias (A fazer, Em andamento, Bloqueada, Concluída) e, dentro delas, na ordem da lista; os cadernos vêm na ordem deles.
- Abaixo do título de cada folha vêm **Status:** e as datas de criação e de alteração; numa folha sozinha, também **Local:**.
- O conteúdo mantém a formatação, e os títulos do conteúdo ficam um nível abaixo do título da folha.

O documento é feito para leitores de telas: no Word, os títulos usam os estilos Título 1, Título 2… e aparecem no painel de navegação; na página HTML, são títulos navegáveis com a tecla H do NVDA. O documento tem o idioma do NVDA e o título nas propriedades.

## Configurações

Abra o menu do NVDA, **Preferências, Configurações**, categoria **Notas Workflow NVDA**.

| Opção | Atalho | Descrição |
|---|---|---|
| Pasta das folhas | Alt+P | A pasta onde fica o arquivo das folhas. |
| Procurar… | Alt+R | Escolhe a pasta numa janela do Windows. |
| Usar a pasta padrão | Alt+D | Volta para a pasta padrão. |
| Salvar automaticamente depois de (segundos) | Alt+S | De 1 a 30 segundos. Padrão: 2. |
| Anunciar o salvamento automático | Alt+A | Marcada, o NVDA fala "Folha salva" a cada salvamento automático. Vem desmarcada para não interromper a digitação. |
| Importar folhas… | Alt+I | Traz folhas de um arquivo `.json` (veja "Cópia de segurança: importar e exportar"). |
| Exportar folhas… | Alt+E | Grava todas as folhas num arquivo `.json`. |
| Manual de uso… | Alt+N | Abre este manual na janela de leitura do NVDA. |

Ao trocar a pasta das folhas e pressionar OK:

- se a pasta nova **já tem** folhas do Notas Workflow NVDA, elas passam a ser usadas ("Usando as folhas da nova pasta");
- se a pasta nova **está vazia**, as folhas atuais são gravadas nela ("Folhas salvas na nova pasta").

A pasta precisa existir e poder ser gravada; senão, as configurações avisam e não fecham.

## Onde ficam as folhas

As folhas ficam no arquivo `NotasWorkflowNVDA-data.json`, na pasta das folhas. A pasta padrão é `%APPDATA%\nvda\NotasWorkflowNVDA` (na versão portátil do NVDA, dentro da pasta do NVDA portátil).

### Segurança dos dados

- Toda mudança é gravada em segundo plano, meio segundo depois da última mudança, de forma segura: um arquivo temporário é escrito e só então troca o antigo, que fica como cópia de segurança `NotasWorkflowNVDA-data.json.bak`. Ao encerrar o NVDA, o que estiver pendente é gravado antes.
- Um arquivo danificado é guardado com outro nome (`NotasWorkflowNVDA-data.corrupt-` e a data) e a cópia de segurança é usada, com aviso. Nenhum arquivo é apagado.
- Se não for possível gravar (disco cheio, pasta sem permissão), as folhas continuam abertas, o NVDA avisa e a próxima mudança tenta de novo.

### Muitas folhas

O complemento foi medido com 100 mil folhas. O NVDA inicia na hora: as folhas são lidas em segundo plano, e um comando usado antes disso faz o NVDA falar "Carregando as folhas…" e esperar. Mudar o status, abrir, salvar e buscar levam frações de segundo. O arquivo pode ter até 200 MB.

### Usar em mais de um computador

Escolha como pasta das folhas uma pasta do **OneDrive** ou do **Google Drive para computador**, que sincronizam o arquivo sozinhos. Ao abrir a janela Notas Workflow NVDA, o complemento percebe se o arquivo mudou em outro computador e lê as folhas de novo.

> **Atenção:** se dois computadores mudarem as folhas ao mesmo tempo, vale a última gravação. A cópia `.bak` guarda a versão anterior.

## Cópia de segurança: importar e exportar

**Exportar folhas… (Alt+E)**, nas configurações, grava todas as folhas, cadernos e pastas num arquivo `.json`, para cópia de segurança ou para levar a outro computador. O NVDA fala "Exportado:" e o número de folhas.

**Importar folhas… (Alt+I)** junta as folhas de um arquivo exportado às suas:

- folhas, cadernos e pastas novos são acrescentados;
- quando o arquivo traz uma folha que você já tem, fica a versão alterada por último;
- dados inválidos são corrigidos ou descartados, e arquivos acima de 200 MB não são abertos.

O NVDA fala "Importado:" com o número de folhas, cadernos e pastas trazidos. Os documentos de **Exportar…** (Word, Markdown e HTML) não podem ser importados de volta.

## Atalhos

### Comandos globais

| Atalho | Ação |
|---|---|
| NVDA+Alt+N | Abrir a janela Notas Workflow NVDA |
| NVDA+Alt+F | Nova folha |
| NVDA+Alt+B | Buscar nas folhas |
| sem atalho | Falar quantas folhas cada raia tem (por exemplo "A fazer 2, Em andamento 1, Bloqueada 0, Concluída 3") |
| sem atalho | Abrir o manual de uso |
| sem atalho | Criar uma folha com o texto de um documento |

Todos podem ser mudados, e os sem atalho podem ganhar um, em **Preferências, Definir comandos**, categoria **Notas Workflow NVDA**.

### Dentro das janelas

| Atalho | Onde | Ação |
|---|---|---|
| Enter | Lista de folhas, Organização, resultados | Abrir a folha |
| Enter | Mostrar | Ir para a lista de folhas |
| Delete | Lista de folhas, Organização | Excluir |
| Alt+Shift+Seta para a direita | Lista de folhas | Status seguinte |
| Alt+Shift+Seta para a esquerda | Lista de folhas | Status anterior |
| Ctrl+Shift+Seta para cima | Lista de folhas | Subir a folha na raia |
| Ctrl+Shift+Seta para baixo | Lista de folhas | Descer a folha na raia |
| Ctrl+Shift+Seta para cima | Mostrar, Organização | Subir a pasta ou o caderno |
| Ctrl+Shift+Seta para baixo | Mostrar, Organização | Descer a pasta ou o caderno |
| Seta para a direita / Seta para a esquerda | Árvores | Abrir / fechar a raia, a pasta ou o ramo |
| F2 | Organização | Renomear (numa folha, mudar o título) |
| Ctrl+S | Janela da folha | Salvar agora |
| Ctrl+B | Conteúdo | Negrito |
| Ctrl+I | Conteúdo | Itálico |
| Esc | Qualquer janela | Fechar (na janela da folha, salva antes) |

## Mensagens faladas

| O NVDA fala | Quando |
|---|---|
| Folha criada em A fazer | Uma folha foi criada, com o status escolhido. |
| Status atualizado para Em andamento | O status da folha mudou. |
| Já está na primeira raia / Já está na última raia | Não há status anterior ou seguinte. |
| Posição 2 de 5 | Ctrl+Shift+Seta para cima ou para baixo mudou a folha, a pasta ou o caderno de lugar. |
| Já está no topo da raia / Já está no fim da raia | A folha já é a primeira ou a última da raia. |
| Já está no topo da lista / Já está no fim da lista | A pasta ou o caderno já é o primeiro ou o último da lista. |
| Aqui só pastas e cadernos mudam de ordem | Ctrl+Shift+Seta para cima ou para baixo em outro item do campo Mostrar ou da árvore Organização. |
| Folhas recentes ficam na ordem da última alteração; aqui a ordem não pode ser mudada | Ctrl+Shift+Seta para cima ou para baixo em Folhas recentes. |
| Agora em: Caderno Trabalho | A folha ou o caderno foi para outro lugar. |
| Folha excluída: título | A folha foi excluída. |
| Folha salva | Ctrl+S, ou o salvamento automático com o anúncio ligado. |
| Negrito, Lista numerada… / Negrito removido | Um formato foi aplicado ou removido. |
| Encontrado: 3 folhas / Nenhuma folha encontrada | Resultado da busca. |
| Caderno … criado, Pasta … criada, Renomeado para …, … excluído | Criar, renomear e excluir cadernos, pastas e folhas. |
| Lendo o documento… | Um documento está sendo lido. |
| Folha criada em A fazer com o texto de Relatório.docx | A folha a partir de documento foi criada. |
| Texto de Relatório.docx inserido | Inserir documento colocou o texto na folha. |
| O texto era longo demais: só a primeira parte foi usada (uma folha guarda até 1 MB). | O documento não coube inteiro na folha. |
| A folha está cheia (até 1 MB): nada foi inserido. | Inserir documento numa folha que já tem o máximo de texto. |
| … não pode ser lido. Escolha um documento do Word (.docx)… | O arquivo escolhido não é de um tipo aceito. |
| Não foi possível ler …: o arquivo está danificado ou protegido por senha. / … não tem texto. / … tem mais de 50 MB e não foi lido. | O documento não pôde ser usado. |
| Exportado: 3 folhas, em Trabalho.docx | Exportar… gravou o documento. |
| Exportado: 3 folhas, um arquivo por folha, na pasta … | Exportar… gravou um arquivo para cada folha. |
| Nada para exportar: … | O caderno ou a pasta escolhida está vazia. |
| Não há cadernos. / Não há pastas. | Exportar… > Caderno… ou Pasta… sem nenhum caderno ou pasta. |
| Não foi possível exportar para … | O documento não pôde ser gravado. |
| Importado: … / Exportado: … | Importar folhas… e Exportar folhas… das configurações. |
| Folhas salvas na nova pasta / Usando as folhas da nova pasta | A pasta das folhas mudou. |
| Carregando as folhas… | Um comando foi usado enquanto as folhas ainda eram lidas, logo depois de o NVDA iniciar. |
| Folhas da versão anterior trazidas para o Notas Workflow NVDA: … | As folhas do antigo NotasWorkflow foram copiadas. |
| Esta folha foi excluída. | A folha aberta foi excluída por outro caminho. |
| As folhas salvas estavam danificadas… | O arquivo estava danificado e foi guardado com outro nome. |
| Não foi possível salvar as folhas em … | Erro de gravação: confira a pasta. |
| Este arquivo não tem folhas do Notas Workflow NVDA. | O arquivo escolhido para importar não é válido. |
| O arquivo tem mais de 200 MB e não foi aberto. | Arquivo grande demais. |
| O nome não pode ficar vazio. | Caderno ou pasta sem nome. |
| O manual de uso não foi encontrado. Instale o complemento de novo. | O arquivo do manual está faltando. |

## Privacidade e segurança

- O complemento **não usa a internet**: nenhuma folha sai do computador, e não há conta nem senha.
- O título e o conteúdo das folhas **nunca** vão para o log do NVDA.
- Excluir sempre pede confirmação, com Não como padrão; ao excluir um caderno ou uma pasta, a pergunta diz quanto será excluído junto.
- Arquivos importados e documentos lidos são conferidos: tamanhos, tipos e identificadores inválidos são corrigidos ou descartados, e o conteúdo nunca é exibido como página nem executado.
- Os documentos exportados levam só o texto e a formatação das folhas, e a página HTML não carrega nada da internet.
- O complemento fica desligado nas telas seguras do Windows (tela de logon e controle de conta de usuário).
- As folhas ficam num arquivo de texto legível na pasta do seu perfil do Windows.

## Perguntas frequentes

### O NVDA diz que não foi possível salvar as folhas

A pasta das folhas não existe mais ou não pode ser gravada (por exemplo, um pen drive removido). Escolha outra pasta nas configurações ou use **Usar a pasta padrão**. As folhas abertas continuam na memória até lá.

### Minhas folhas sumiram depois de trocar a pasta

A pasta nova já tinha folhas do Notas Workflow NVDA, e elas passaram a ser usadas. Volte à pasta anterior nas configurações: as folhas antigas continuam lá.

### O arquivo estava danificado

O complemento guardou o arquivo danificado com o nome `NotasWorkflowNVDA-data.corrupt-` seguido da data e usou a cópia de segurança. O arquivo guardado nunca é apagado.

### Não encontro uma folha numa raia com muitas folhas

Cada raia mostra 200 folhas por vez. Use "Mostrar mais" no fim da raia, o campo Mostrar para ver só um caderno ou uma pasta, ou a busca (NVDA+Alt+B), que encontra a folha e a mostra selecionada ao voltar.

### Um caderno não sobe acima de outra pasta

Com Ctrl+Shift+Setas, um caderno só muda de lugar entre os cadernos da mesma pasta. Para levá-lo a outra pasta (ou para Sem pasta), use **Mover para…** em Cadernos e pastas.

### Escrevi um asterisco e ele sumiu

Pares de asteriscos em volta de uma palavra viram itálico (`*palavra*`). Para mostrar asteriscos, use-os no meio de palavras ou números, como `2*3`.
