# SDD do Notas Workflow NVDA

Documento de projeto de software (Software Design Document) do complemento **NotasWorkflowNVDA** para o leitor de telas NVDA. Ele define **o que** o complemento faz, **como** é construído, **como** é testado e **como** uma versão é liberada. Vale para todas as versões a partir da 1.0.0.

* Pasta do projeto: `C:\git\ADDONS NVDA\NotasWorkflowNVDA`
* Projeto de referência: aplicação web **Notas Workflow** (`C:\git\notasworkflow`, Next.js), cujo SDD está em `C:\git\notasworkflow\SDD.md`
* Nome interno do complemento: `NotasWorkflowNVDA` (pacote `dist/NotasWorkflowNVDA-<versão>.nvda-addon`)
* Autor: Wellington Cruz
* Licença: GPL 2 (a mesma do NVDA)

---

## 1. Objetivo

Levar para dentro do NVDA o mesmo fluxo de trabalho do Notas Workflow web: **folhas** (notas) organizadas em **raias** de status (A fazer, Em andamento, Bloqueada, Concluída), agrupadas em **cadernos** e **pastas**, com edição de conteúdo, tags, busca e movimentação entre raias, tudo por teclado, com respostas faladas e sem depender de navegador nem de leitura de página web.

O complemento não é uma cópia visual do quadro kanban: ele traduz cada parte do quadro para controles nativos do Windows que o NVDA lê sem esforço (árvore, tabela, campos e botões), mantendo **o mesmo modelo de dados** do web, de forma que as folhas possam ir e voltar entre os dois.

## 2. Correspondência com o projeto web

O projeto web foi explorado módulo a módulo. Cada módulo tem um equivalente no complemento:

| Projeto web (`C:\git\notasworkflow`) | O que faz no web | Equivalente no complemento |
|---|---|---|
| `types/index.ts` (`Note`, `Notebook`, `Folder`, `Lane`, `DEFAULT_LANES`) | Modelo de dados e as 4 raias padrão | `model.py`: mesmos campos (camelCase), mesmos IDs de raia (`todo`, `inprogress`, `blocked`, `done`) e mesmas cores |
| `lib/store.ts` (Zustand) | Criar, alterar, excluir e mover folhas; criar, renomear e excluir cadernos e pastas; filtro ativo | `store.py` (`NotesStore`): as mesmas operações, com as mesmas regras (excluir caderno solta as folhas; excluir pasta solta cadernos e folhas; cores em rodízio) |
| `lib/storage.ts` (`localStorage`, prefixo `notas-workflow:`) | Persistência no navegador | `store.py`: arquivo JSON `NotasWorkflowNVDA-data.json` com gravação atômica e cópia de segurança; importação e exportação no formato do web |
| `lib/utils.ts` (`textSearch`, `extractExcerpt`, `formatDate`) | Busca textual, trecho e datas | `search.py` (mesma pontuação: termos encontrados / termos da busca; trecho de 120 caracteres) e `messages.formatDate` |
| `app/api/search/route.ts` + Groq | Busca semântica com *embeddings*, com recurso à busca textual | `search.py`: só a busca textual, agora sem diferenciar acentos e maiúsculas (ver seção 10) |
| `components/board/Board.tsx`, `Lane.tsx`, `NoteCard.tsx` | Quadro kanban e layout de tabela, arrastar e soltar, "Mover para", Shift+Alt+Setas | `mainDialog.py`: **árvore de raias** ou **tabela**; botão **Mover para…**; Alt+Shift+Seta para a direita/esquerda muda a raia |
| `components/layout/NewSheetModal.tsx` | Nova folha: título, caderno, status | `noteDialog.NewNoteDialog`: mesmos campos; depois de criar, abre o editor |
| `app/app/note/[id]/page.tsx` + `components/editor/*` (TipTap) | Editor com título, caderno, tags, conteúdo rico, barra de formatação, salvamento automático a cada 2 s | `noteDialog.NoteDialog`: título, caderno, status, tags, conteúdo, menu **Formatação…**, salvamento automático (2 s, configurável) |
| `components/layout/Header.tsx` (menus Novo, Folhas, Cadernos, Pastas) | Criar folha/caderno/pasta e filtrar | Caixa **Mostrar** (todas, soltas, recentes, cada caderno, cada pasta) e janela **Cadernos e pastas…** |
| `components/layout/Sidebar.tsx` (Folhas recentes) | As 10 folhas alteradas por último | Opção **Folhas recentes** da caixa Mostrar |
| `app/app/search/page.tsx` + `SearchBar.tsx` | Página de busca com trecho e relevância | `searchDialog.py`: busca enquanto digita (300 ms), resultados com trecho e relevância |
| `app/app/settings/page.tsx` | Conta, local de armazenamento, acessibilidade | `settingsPanel.py`: pasta das folhas, salvamento automático, importar e exportar |
| `app/login`, `lib/auth.ts` (NextAuth Google/Microsoft) | Login para Drive/OneDrive (ainda simulado no web) | Não há login: as folhas ficam no computador. Para sincronizar, a pasta das folhas pode ficar dentro da pasta do OneDrive ou do Google Drive para computador (ver seção 10) |

## 3. Requisitos

### 3.1 Requisitos funcionais (RF)

| ID | Requisito | Como é atendido |
|---|---|---|
| RF-01 | Criar folha, caderno e pasta | Botão **Criar…** (menu Folha…, Caderno…, Pasta…) na janela principal e em Cadernos e pastas; NVDA+Alt+F cria uma folha de qualquer lugar. Nova folha: título obrigatório (até 200 caracteres), **Local** (solta, uma pasta ou um caderno; padrão: o filtro em uso), status (padrão: a raia selecionada); ao criar, abre o editor. Caderno criado com uma pasta selecionada ou filtrada nasce nela |
| RF-02 | Editar título, local, status, tags e conteúdo | Janela da folha; tags separadas por vírgula (sem repetição, até 30, cada uma até 50 caracteres); conteúdo com marcação leve convertida para HTML |
| RF-03 | Salvamento automático | 2 s (1 a 30, configurável) depois da última alteração; Ctrl+S salva na hora; fechar a janela (Esc ou Salvar e fechar) e encerrar o NVDA com a folha aberta sempre salvam o que estiver pendente — nada se perde |
| RF-04 | Formatação do conteúdo | Menu Formatação… e atalhos: negrito (Ctrl+B), itálico (Ctrl+I), tachado, código, título 2, título 3, lista com marcadores, lista numerada, citação e divisor — as mesmas opções da barra do editor web |
| RF-05 | Ver as folhas por raia | Árvore (a única visualização): cada raia é um ramo com o número de folhas ("A fazer, 3 folhas"); **as raias começam fechadas** (1.3.0) e ficam como a pessoa as deixou; a raia de uma folha selecionada pelo complemento abre sozinha; cada folha mostra título, local, tags e data; **Enter abre a folha** |
| RF-06 | Listas longas | Cada raia (e cada caderno ou pasta na janela Cadernos e pastas) mostra 200 folhas por vez, com o item "Mostrar mais 200 folhas (N ainda não mostradas)"; uma folha a selecionar além da página faz a página dela aparecer |
| RF-07 | Atualizar o status da tarefa | Botão **Atualizar o status da tarefa…** (menu com os outros status) e Alt+Shift+Seta para a direita/esquerda (status seguinte/anterior); a seleção acompanha a folha e o NVDA fala o novo status. Status ou local mudados **na janela da folha** (1.3.0): ao fechar, o foco vai para a próxima folha da mesma raia (a anterior, se era a última; a raia, se era a única) |
| RF-08 | Mover para um caderno ou uma pasta | Botão **Mover para…** (na janela principal e em Cadernos e pastas) e campo Local da janela da folha: folha solta, direto numa pasta ou num caderno; a lista começa no lugar atual |
| RF-09 | Excluir folha | Botão Excluir ou tecla Delete, sempre com confirmação |
| RF-10 | Filtrar | Caixa **Mostrar**: Todas as folhas, Folhas soltas, Folhas recentes (10 alteradas por último), Caderno: <nome>, Pasta: <nome> (folhas da pasta e dos cadernos dentro dela) |
| RF-11 | Cadernos e pastas | Janela **Cadernos e pastas…**: árvore com cada pasta, os cadernos dela e as folhas guardadas nela, cada caderno com as suas folhas, o ramo "Sem pasta" e o ramo "Folhas soltas"; as folhas são carregadas só ao abrir o ramo; Enter abre a folha; Criar…, Renomear… (também o título da folha, F2), Mover para…, Excluir (com confirmação; as folhas nunca são apagadas ao excluir caderno ou pasta) |
| RF-12 | Buscar | Janela **Buscar** (NVDA+Alt+B): título, conteúdo e tags; sem diferenciar acentos e maiúsculas; resultados por relevância, com trecho e porcentagem; Enter abre a folha |
| RF-13 | Guardar as folhas | Arquivo JSON na pasta das folhas (padrão: pasta de configuração do NVDA, subpasta `NotasWorkflowNVDA`); gravação atômica; cópia de segurança do arquivo anterior; arquivo danificado é preservado e a cópia de segurança é usada |
| RF-14 | Trocar a pasta das folhas | Configurações: se a pasta nova já tiver folhas, passam a ser usadas; senão as folhas atuais são gravadas nela |
| RF-15 | Importar e exportar | Arquivo JSON no formato do web (`{"notes": [...], "notebooks": [...], "folders": [...]}`, ou só a lista de folhas); importar junta por ID e fica com a versão alterada por último; dados inválidos são corrigidos ou descartados |
| RF-16 | Resumo das raias | Comando sem atalho padrão: fala quantas folhas há em cada raia |
| RF-18 | Novo nome (1.1.0) | O complemento passou de NotasWorkflow para Notas Workflow NVDA (nome interno NotasWorkflowNVDA). No primeiro início, copia uma vez as configurações da seção [NotasWorkflow] e as folhas da pasta padrão antiga; numa pasta escolhida, copia NotasWorkflow-data.json para o nome novo. Nada do complemento antigo é movido ou apagado, e a cópia é anunciada |
| RF-17 | Atualização externa | Ao abrir a janela, se o arquivo foi mudado por outro computador (pasta sincronizada), as folhas são lidas de novo |

### 3.2 Requisitos de acessibilidade (RA)

| ID | Requisito |
|---|---|
| RA-01 | Todo controle que recebe foco tem nome acessível lido pelo NVDA (também conferido pelo MSAA do Windows) |
| RA-02 | Todo botão e rótulo tem letra de atalho com Alt, sem repetição na mesma janela, em inglês e em português |
| RA-03 | Ordem de tabulação lógica em todas as janelas (seção 5) |
| RA-04 | Tudo funciona só pelo teclado: Enter abre, Delete exclui, Alt+Shift+Setas move, Esc fecha; nenhum arrastar e soltar é necessário (WCAG 2.5.7 do web) |
| RA-05 | Toda ação e todo erro são anunciados em fala curta, sem jargão técnico (equivalente às *live regions* do web, WCAG 4.1.3) |
| RA-06 | O foco nunca se perde: depois de criar, mover, excluir ou fechar, volta para a folha certa (ou para a vizinha) |
| RA-07 | Toda janela tem título próprio; a janela da folha tem o título da folha |
| RA-08 | O rótulo da lista diz o que ela mostra e quantas folhas tem ("Folhas: Caderno Trabalho (4)") |
| RA-09 | Botões que não servem para o item selecionado ficam indisponíveis e saem da tabulação |
| RA-10 | Toda frase da interface é traduzível e está traduzida para português do Brasil, com comentário para tradutores |
| RA-11 | Atalhos padrão não conflitam com os comandos do NVDA nem com os dos outros complementos instalados |
| RA-12 | Comandos aparecem na categoria "Notas Workflow NVDA" de Definir comandos, cada um com descrição |
| RA-13 | A informação nunca depende de cor: a raia é sempre dita pelo nome (WCAG 1.4.1 do web) |

### 3.3 Requisitos de segurança e privacidade (RS)

| ID | Requisito |
|---|---|
| RS-01 | Nenhum acesso à rede: o complemento não importa `socket`, `urllib`, `http` nem `ssl` |
| RS-02 | O conteúdo das folhas nunca vai para o log do NVDA, nem em erros |
| RS-03 | Só JSON: nenhum `eval`, `exec`, `pickle`, `subprocess` ou shell |
| RS-04 | Arquivos de dados e de importação acima de 200 MB são recusados sem ler tudo |
| RS-05 | Dados importados ou lidos são validados: tipos, tamanhos (título 200, tag 50, conteúdo 1 MB), IDs (só letras, números, `-` e `_`, até 64), raias conhecidas, referências a cadernos e pastas existentes |
| RS-06 | O HTML do conteúdo nunca é executado nem exibido como página: é convertido em texto por um analisador que descarta `script`, `style` e atributos; o HTML gerado escapa tudo o que a pessoa digitou (sem injeção quando o web abrir a folha) |
| RS-07 | Gravação atômica (arquivo temporário + `os.replace`) com cópia de segurança: queda de energia ou erro não corrompe as folhas |
| RS-08 | Nenhum caminho de arquivo vem dos dados: o nome do arquivo é fixo; a pasta e os arquivos de importação/exportação são escolhidos pela pessoa |
| RS-09 | Excluir folha, caderno ou pasta sempre pede confirmação; excluir caderno ou pasta nunca apaga folhas |
| RS-10 | Complemento desligado nas telas seguras (logon, controle de conta) |
| RS-11 | Desinstalar **não apaga** as folhas (são documentos da pessoa); a documentação diz onde ficam |

### 3.4 Restrições

* Somente biblioteca padrão do Python e módulos do NVDA: sem dependências externas e sem DLLs próprias. Os módulos usados precisam existir no Python embutido no NVDA (`library.zip`); já conferido: `uuid`, `html.parser`, `unicodedata`, `datetime`, `json`, `threading`, `heapq`.
* Compatível com NVDA 2024.1 (Python 3.11, 32 bits) até 2026.x (Python 3.13, 64 bits).
* Indentação com tabulação, como no NVDA. Texto da interface em inglês no código, traduzido para pt_BR (`.po`).
* Datas gravadas como o `toISOString()` do JavaScript (`2026-10-12T18:41:00.000Z`, UTC), para o web ler sem conversão.

## 4. Arquitetura

```
NVDA
 └─ globalPlugins/NotasWorkflowNVDA/
     __init__.py        GlobalPlugin: atalhos, menu Ferramentas, painel, leitura em segundo plano, criar/mover/excluir
     model.py           Raias, criação e validação de folhas, cadernos e pastas, filtros, datas ISO
     markup.py          Marcação leve <-> HTML; HTML -> texto; formatação de seleção
     search.py          Índice da busca (texto preparado de cada folha), normalização sem acentos, pontuação, trecho
     store.py           NotesStore: operações, índice por id, arquivo JSON com gravação em segundo plano
     messages.py        Textos traduzidos: raias, contagens, lugares, datas, descrição das folhas
     prompts.py         Menus e caixas de escolha compartilhados pelas janelas
     mainDialog.py      Janela "Notas Workflow NVDA": Mostrar, árvore de raias paginada, ações
     noteDialog.py      Janelas "Nova folha" e da folha (editor)
     searchDialog.py    Janela "Buscar folhas"
     organizeDialog.py  Janela "Cadernos e pastas" (com as folhas, carregadas ao abrir cada ramo)
     settingsPanel.py   Configurações do NVDA > Notas Workflow NVDA
```

Camadas:

1. **Núcleo sem interface** (`model`, `markup`, `search`, `store`): não importa `wx` nem módulos do NVDA; é testado em Python 3.11 e 3.13.
2. **Interface** (`messages`, `prompts`, `mainDialog`, `noteDialog`, `searchDialog`, `organizeDialog`, `settingsPanel`): wxPython e `gui.guiHelper` do NVDA.
3. **Integração** (`__init__`): scripts, menu Ferramentas, registro do painel. A interface roda na linha principal do NVDA; a leitura do arquivo, a preparação da busca e a gravação rodam em linhas de execução próprias (seção 4.6).

### 4.1 Modelo de dados (igual a `types/index.ts`)

```json
{
  "format": "notas-workflow",
  "version": 1,
  "folders":   [{"id": "…", "name": "Projetos", "color": "#FF9500", "createdAt": "…"}],
  "notebooks": [{"id": "…", "name": "Trabalho", "color": "#007AFF", "folderId": "… ou null", "createdAt": "…"}],
  "notes": [{
    "id": "uuid-v4", "title": "Título", "content": "<p>HTML do TipTap</p>",
    "tags": ["trabalho"], "laneId": "todo", "notebookId": "… ou null", "folderId": "… ou null",
    "createdAt": "2026-10-12T18:41:00.000Z", "updatedAt": "2026-10-12T18:41:00.000Z"
  }]
}
```

Raias (`DEFAULT_LANES` do web): `todo` A fazer (#007AFF), `inprogress` Em andamento (#FF9500), `blocked` Bloqueada (#FF2D55), `done` Concluída (#34C759). A cor é guardada para o web, mas o complemento sempre diz o **nome**.

A ordem das folhas dentro de uma raia é a ordem de criação (a mesma de `Object.values(notes)` no web).

### 4.2 Conteúdo: marcação leve e HTML

O editor do web (TipTap StarterKit) grava HTML. Um editor rico não é bem lido por leitores de tela dentro de uma caixa de diálogo, então o complemento edita o conteúdo como **texto puro com marcação leve** e converte nos dois sentidos:

| No editor do complemento | HTML gravado (TipTap) |
|---|---|
| uma linha de texto | `<p>texto</p>` |
| linha vazia | `<p></p>` |
| `## Título` / `### Título` | `<h2>` / `<h3>` (`#` vira `<h1>`) |
| `- item` ou `* item` | `<ul><li><p>item</p></li></ul>` |
| `1. item` | `<ol><li><p>item</p></li></ol>` |
| `> citação` | `<blockquote><p>citação</p></blockquote>` |
| `---` | `<hr>` |
| linhas entre ```` ``` ```` | `<pre><code>…</code></pre>` |
| `**negrito**`, `*itálico*`, `~~tachado~~`, `` `código` `` | `<strong>`, `<em>`, `<s>`, `<code>` |

* Todo texto digitado é escapado antes de virar HTML (`<script>` vira `&lt;script&gt;`).
* `*` só vira itálico em começo e fim de palavra (`2*3*4` continua igual).
* HTML vindo do web é lido por `html.parser`: marcas desconhecidas viram só texto; `script` e `style` são descartados com o conteúdo.
* O texto gerado pelo complemento vai e volta sem perda (texto → HTML → texto).

### 4.3 Armazenamento

* Arquivo `NotasWorkflowNVDA-data.json` na pasta das folhas. Padrão: `%APPDATA%\nvda\NotasWorkflowNVDA\` (pasta de configuração do NVDA; na versão portátil, a pasta do NVDA portátil).
* Toda alteração pede uma gravação; uma linha de execução própria espera 0,5 s sem novas alterações (várias viram uma gravação só) e então escreve `NotasWorkflowNVDA-data.json.tmp` (JSON compacto, folha por folha, com pausas para o NVDA continuar respondendo), guarda o arquivo anterior como `NotasWorkflowNVDA-data.json.bak` e troca com `os.replace` (atômico no Windows). Ao encerrar, o complemento espera a última gravação.
* Ao ler: arquivo ausente = nenhuma folha; JSON danificado ou acima de 200 MB = o arquivo é renomeado para `NotasWorkflowNVDA-data.corrupt-<data>.json` (nunca apagado), a cópia `.bak` é usada se estiver boa e a pessoa é avisada.
* Erro de gravação (disco cheio, pasta somente leitura): as folhas continuam na memória, a pessoa é avisada e a próxima alteração tenta de novo.
* Mudanças externas: o tamanho e a data do arquivo são lembrados; ao abrir a janela principal, se mudaram, o arquivo é lido de novo.

### 4.4 Busca (equivalente a `textSearch` e `extractExcerpt`)

1. A busca e o texto da folha (título, conteúdo sem marcação e tags) são normalizados: minúsculas (`casefold`) e sem acentos (NFKD sem marcas).
2. Pontuação = termos encontrados ÷ termos da busca (igual ao web). Desempate: termos encontrados no título, depois a folha alterada por último.
3. Trecho: até 120 caracteres em volta do primeiro termo encontrado, com "…" nas pontas (igual ao web, mas achando o termo sem acento).
4. Resultados com pontuação zero não aparecem; no máximo 100.

### 4.6 Desempenho (1.2.0)

Requisitos não funcionais, medidos com 100 mil folhas em 80 cadernos e 12 pastas (`tests/test_performance.py`, limites folgados para não falhar em máquina ocupada):

| ID | Requisito | Como é atendido | Medido |
|---|---|---|---|
| RNF-01 | O NVDA inicia sem esperar as folhas | Leitura do arquivo numa linha de execução; todo comando chama `ensureLoaded()` e, se preciso, fala "Carregando as folhas…" e espera | 0 s para o complemento ficar pronto; 3 a 5 s para ler |
| RNF-02 | Busca em fração de segundo | `SearchIndex`: texto de cada folha preparado uma vez (sem marcação, sem acentos), refeito só quando a folha muda (comparação por identidade dos objetos); preparado em segundo plano em lotes com pausas; só os 100 melhores resultados são ordenados | 0,1 a 0,5 s |
| RNF-03 | Mudar o status e editar sem travar | A árvore só refaz as raias afetadas (`refreshLanes`) ou troca o texto de um item (`noteChanged`); índice por id no store (`getNote` em O(1)) | 0,2 a 0,4 s |
| RNF-04 | Gravar sem travar | Gravação em segundo plano, adiada e agrupada; JSON codificado folha por folha com pausas, porque `json.dumps` do arquivo inteiro prende o Python por cerca de 1 s | 0 s para quem usa; 2 a 4 s em segundo plano |
| RNF-05 | Árvores leves | Páginas de 200 folhas por raia; folhas de Cadernos e pastas carregadas só ao abrir o ramo; contagem de folhas por lugar numa passada só; a janela principal é escondida ao fechar e reaproveitada | Reabrir: 0 s |

A seleção da árvore é feita junto com o "item com foco" do Windows (`SetFocusedItem`): sem isso, a seleção podia voltar a um item antigo quando a árvore recebia o foco.

### 4.5 Erros

| Situação | Fala (pt_BR) |
|---|---|
| Arquivo danificado | As folhas salvas estavam danificadas. O arquivo foi guardado como <nome> e a cópia de segurança foi usada. |
| Não foi possível gravar | Não foi possível salvar as folhas em <pasta>. Confira se a pasta existe e pode ser gravada. |
| Importação inválida | Este arquivo não tem folhas do Notas Workflow NVDA. |
| Arquivo grande demais | O arquivo tem mais de 200 MB e não foi aberto. |
| Título vazio | O botão Criar fica indisponível até haver título |
| Folha excluída enquanto aberta | Esta folha foi excluída. |

## 5. Interface

### 5.1 Janela Notas Workflow NVDA (NVDA+Alt+N ou Ferramentas > Notas Workflow NVDA…)

Ordem de tabulação:

1. **Mostrar** (caixa): Todas as folhas, Folhas soltas, Folhas recentes, Caderno: <nome>…, Pasta: <nome>…
2. **Folhas** (árvore de raias; o rótulo diz o filtro e quantas folhas há): ramos "A fazer, 2 folhas"… fechados no início (só a raia da folha selecionada abre); cada folha: "Título, caderno Trabalho, tags x, y, atualizada em 12/10/2026"; 200 folhas por raia e o item "Mostrar mais". Enter abre, Delete exclui, Alt+Shift+Seta para a direita/esquerda muda o status.
3. Botões: **Criar…** (menu Folha…, Caderno…, Pasta…), **Atualizar o status da tarefa…**, **Mover para…**, **Excluir**, **Buscar…**, **Cadernos e pastas…**, **Fechar** (Esc).

A janela é única. Fechar só a esconde; abrir de novo a mostra na hora, lendo o arquivo de novo se outro computador o mudou.

### 5.2 Nova folha (NVDA+Alt+F ou Criar… > Folha…)

**Título** (obrigatório), **Local** (Folha solta, cada pasta e cada caderno com a pasta dele), **Status** (as 4 raias), **Criar** (padrão; indisponível sem título) e **Cancelar**. Enter cria; Esc cancela. Depois de criar, a janela da folha abre com o foco no conteúdo.

### 5.3 Janela da folha (editor)

Título da janela = título da folha. Ordem: **Título**, **Local**, **Status**, **Tags (separadas por vírgula)**, **Conteúdo** (várias linhas), **Formatação…**, **Situação do salvamento** (somente leitura: "Salva às 14:32", "Alterações não salvas…"), **Salvar e fechar**. Esc também salva e fecha. Ctrl+S salva sem fechar; Ctrl+B e Ctrl+I formatam no conteúdo.

### 5.4 Buscar folhas (NVDA+Alt+B)

**Buscar** (campo; busca 300 ms depois de parar de digitar, ou com Enter), **Resultados** (tabela: Título, Trecho, Relevância, Atualizada em; Enter abre), **Abrir**, **Fechar**. O NVDA fala "Encontrado: N folhas" ou "Nenhuma folha encontrada".

### 5.5 Cadernos e pastas

**Organização** (árvore: cada pasta com os seus cadernos e as folhas guardadas nela; cada caderno com as suas folhas; "Sem pasta"; "Folhas soltas"; folhas lidas com título, status, tags e data; Enter abre), **Criar…**, **Renomear…** (F2), **Mover para…**, **Excluir** (Delete), **Fechar**.

### 5.6 Configurações do NVDA > Notas Workflow NVDA

**Pasta das folhas** (campo), **Procurar…**, **Usar a pasta padrão**, **Salvar automaticamente depois de (segundos)** (1–30, padrão 2), **Anunciar o salvamento automático** (padrão desligado, para não interromper a digitação), **Importar folhas…**, **Exportar folhas…**.

## 6. Atalhos padrão

Verificados contra o NVDA 2026.1.1 instalado (NVDA+Alt+C, M, R, S, T, Home, End e Tab são do NVDA) e os complementos instalados (NVDAIAs: NVDA+Alt+I e D; SpotifyNVDA: P, A, U, Espaço e Setas; AccessibilityWHATSAPP: W).

| Ação | Atalho |
|---|---|
| Abrir a janela Notas Workflow NVDA | NVDA+Alt+N |
| Nova folha | NVDA+Alt+F |
| Buscar folhas | NVDA+Alt+B |
| Falar o resumo das raias | sem atalho (pode ser definido em Definir comandos) |

Dentro das janelas: Enter abre, Delete exclui, Alt+Shift+Seta para a direita/esquerda muda a raia, Ctrl+S salva, Ctrl+B negrito, Ctrl+I itálico, Esc fecha.

## 7. Dados guardados

A documentação de uso tem duas formas: o `readme` curto, que vai dentro do pacote (ajuda do complemento no NVDA), e o **manual detalhado em Word**, `docs/Manual-NotasWorkflowNVDA.docx`, gerado de `docs/manual/MANUAL.md` por `docs/manual/gerar_manual.py` (só biblioteca padrão). O manual usa os estilos de título do Word, sumário com links, tabelas com cabeçalho repetido e idioma pt-BR, para ser lido com o NVDA.

| Dado | Onde | Proteção |
|---|---|---|
| Pasta das folhas, salvamento automático, anunciar, visualização | `nvda.ini`, seção `[NotasWorkflowNVDA]` | Não são segredos |
| Folhas, cadernos e pastas | `<pasta das folhas>\NotasWorkflowNVDA-data.json` (+ `.bak`) | Permissões do perfil do Windows; JSON legível, como o `localStorage` do web |

## 8. Plano de testes

O detalhamento de cada caso fica em [SDD-TESTES.md](SDD-TESTES.md). Resumo:

| Suíte | Arquivo | Tipo |
|---|---|---|
| Unidades (Python 3.11 e 3.13) | `tests/test_pure.py` | Modelo, regras do `lib/store.ts`, marcação ↔ HTML, busca, arquivo, importação |
| Interface | `tests/test_gui.py` | Janelas reais em wxPython: criar, editar, salvar automaticamente, mover, excluir, filtrar, buscar, cadernos e pastas, configurações, comandos |
| Acessibilidade | `tests/test_accessibility.py` | Rótulos, letras de atalho, tabulação, foco, fala, títulos, nomes lidos pelo MSAA, conflito de atalhos (inglês e português) |
| Tradução | `tests/test_translation.py` | Interface toda em português, marcadores iguais, atalhos preservados |
| Segurança | `tests/test_security.py` | bandit, padrões proibidos, sem rede, sem conteúdo no log, validação, HTML hostil, gravação atômica, limites de tamanho |
| NVDA real | `tests/test_nvda_runtime.py` | Todo módulo importado existe no Python do NVDA instalado; manifesto aceito |
| Pacote | `tests/run_all.py` | `build.py` gera um pacote válido |
| Desempenho | `tests/test_performance.py` | 100 mil folhas: início, leitura, janela, status, edição, gravação, busca, Cadernos e pastas, saída (seção 4.6) |
| Manual | `tests/test_manual.py` | Manual em Word atualizado, da versão atual, com todos os controles, raias, formatos e atalhos, e acessível |

O que não é automatizável (fala real do NVDA, pasta sincronizada com OneDrive, troca de arquivos com o web) está no roteiro manual [TESTES-MANUAIS.md](TESTES-MANUAIS.md).

## 9. Processo de versão (obrigatório em toda nova versão)

1. Atualizar `version` e `changelog` em `addon/manifest.ini` e `addon/locale/pt_BR/manifest.ini`, e o `CHANGELOG.md`.
2. Atualizar o manual de uso em Word: editar `docs/manual/MANUAL.md` (fonte) e acrescentar a versão em "Histórico deste manual"; o `build.py` gera `docs/Manual-NotasWorkflowNVDA.docx`. Vale para toda alteração de comportamento ou de interface.
3. Escrever ou atualizar os testes das funções novas ou alteradas e acrescentar os casos no `SDD-TESTES.md`.
4. Rodar **todas** as suítes: `python tests/run_all.py --note "o que mudou"`.
5. Se algo falhar: registrar em `reports/PROBLEMAS-<versão>.md` (ID, gravidade, causa, correção), corrigir e rodar de novo até **0 falhas**.
6. Gerar `reports/RELATORIO-TESTES-<versão>.md` com os números de `reports/execucoes.json`.
7. Só então gerar o pacote com `python build.py --release`, que **roda todas as suítes de novo e recusa gerar o pacote se algum teste falhar**.

## 10. Riscos e decisões

| Risco ou diferença | Decisão |
|---|---|
| Busca semântica do web (Groq + *embeddings*) | No web os *embeddings* nunca são gerados (não existe `/api/embed`), então ele sempre cai na busca textual. O complemento faz a mesma busca textual, melhorada (sem acentos, desempate pelo título) e **sem rede**: nenhuma chave de API a guardar e nenhum texto das folhas sai do computador. Busca semântica fica para uma versão futura, se o web passar a gerar *embeddings* |
| Login Google/Microsoft e Drive/OneDrive | No web ainda é só a tela (as folhas ficam no `localStorage`). O complemento não pede login: a pasta das folhas pode ficar dentro da pasta sincronizada do OneDrive ou do Google Drive, que fazem a sincronização sozinhos |
| Dois computadores mudando a mesma pasta sincronizada ao mesmo tempo | O arquivo é lido de novo ao abrir a janela; a última gravação vence. A cópia `.bak` guarda a versão anterior. Documentado no manual |
| Editor rico (TipTap) em leitor de tela | Texto puro com marcação leve, conversão sem perda para o HTML do TipTap; formatação por menu e atalhos |
| Arrastar e soltar do quadro | Substituído por Mover para… e Alt+Shift+Setas, que o próprio web já oferece como alternativa de teclado |
| Folhas sensíveis | Ficam em JSON legível na pasta do perfil (como o `localStorage` do web). Criptografia impediria abrir as folhas no outro computador da pasta sincronizada; avaliar em versão futura como opção |
| Filtro por pasta do web (compara `notebookId` com o ID da pasta, um defeito) | O complemento mostra as folhas da pasta e as dos cadernos que estão nela |
| Troca de nome (1.1.0): o NVDA trata NotasWorkflowNVDA como outro complemento, ao lado do NotasWorkflow | Migração só por cópia, uma vez (configuração legacyChecked), com aviso falado pedindo para desinstalar o antigo; o formato de dados notas-workflow não muda |
| Desinstalar apagaria documentos | O complemento não apaga as folhas ao ser desinstalado |
