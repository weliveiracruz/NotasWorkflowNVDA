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
| RF-01 | Criar folha com título, caderno e status | Janela **Nova folha** (NVDA+Alt+F, botão Nova folha… ou menu Ferramentas); título obrigatório (até 200 caracteres); caderno opcional ("Folha solta"); status padrão "A fazer" ou a raia selecionada; ao criar, abre o editor |
| RF-02 | Editar título, caderno, status, tags e conteúdo | Janela da folha; tags separadas por vírgula (sem repetição, até 30, cada uma até 50 caracteres); conteúdo com marcação leve convertida para o HTML do TipTap |
| RF-03 | Salvamento automático | 2 s (1 a 30, configurável) depois da última alteração; Ctrl+S salva na hora; fechar a janela (Esc ou Salvar e fechar) e encerrar o NVDA com a folha aberta sempre salvam o que estiver pendente — nada se perde |
| RF-04 | Formatação do conteúdo | Menu Formatação… e atalhos: negrito (Ctrl+B), itálico (Ctrl+I), tachado, código, título 2, título 3, lista com marcadores, lista numerada, citação e divisor — as mesmas opções da barra do editor web |
| RF-05 | Ver as folhas por raia | Árvore: cada raia é um ramo com o número de folhas ("A fazer, 3 folhas"); cada folha mostra título, caderno, tags e data |
| RF-06 | Ver as folhas em tabela | Lista com colunas Título, Status, Caderno, Tags e Atualizada em (layout "tabela" do web) |
| RF-07 | Mover folha entre raias | Botão **Mover para…** (menu com as outras raias, como no cartão do web) e Alt+Shift+Seta para a direita/esquerda (próxima/anterior raia, como o Shift+Alt+Setas do web); a seleção acompanha a folha e o NVDA fala a raia nova |
| RF-08 | Mudar o caderno de uma folha | Botão **Mudar caderno…** e campo Caderno da janela da folha |
| RF-09 | Excluir folha | Botão Excluir ou tecla Delete, sempre com confirmação |
| RF-10 | Filtrar | Caixa **Mostrar**: Todas as folhas, Folhas soltas, Folhas recentes (10 alteradas por último), Caderno: <nome>, Pasta: <nome> (folhas da pasta e dos cadernos dentro dela) |
| RF-11 | Cadernos e pastas | Janela **Cadernos e pastas…**: novo caderno (dentro da pasta selecionada), nova pasta, renomear, mover caderno para outra pasta, excluir (com confirmação; as folhas nunca são apagadas, ficam soltas) |
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
| RS-04 | Arquivos de dados e de importação acima de 20 MB são recusados sem ler tudo |
| RS-05 | Dados importados ou lidos são validados: tipos, tamanhos (título 200, tag 50, conteúdo 1 MB), IDs (só letras, números, `-` e `_`, até 64), raias conhecidas, referências a cadernos e pastas existentes |
| RS-06 | O HTML do conteúdo nunca é executado nem exibido como página: é convertido em texto por um analisador que descarta `script`, `style` e atributos; o HTML gerado escapa tudo o que a pessoa digitou (sem injeção quando o web abrir a folha) |
| RS-07 | Gravação atômica (arquivo temporário + `os.replace`) com cópia de segurança: queda de energia ou erro não corrompe as folhas |
| RS-08 | Nenhum caminho de arquivo vem dos dados: o nome do arquivo é fixo; a pasta e os arquivos de importação/exportação são escolhidos pela pessoa |
| RS-09 | Excluir folha, caderno ou pasta sempre pede confirmação; excluir caderno ou pasta nunca apaga folhas |
| RS-10 | Complemento desligado nas telas seguras (logon, controle de conta) |
| RS-11 | Desinstalar **não apaga** as folhas (são documentos da pessoa); a documentação diz onde ficam |

### 3.4 Restrições

* Somente biblioteca padrão do Python e módulos do NVDA: sem dependências externas e sem DLLs próprias. Os módulos usados precisam existir no Python embutido no NVDA (`library.zip`); já conferido: `uuid`, `html.parser`, `unicodedata`, `tempfile`, `datetime`, `json`.
* Compatível com NVDA 2024.1 (Python 3.11, 32 bits) até 2026.x (Python 3.13, 64 bits).
* Indentação com tabulação, como no NVDA. Texto da interface em inglês no código, traduzido para pt_BR (`.po`).
* Datas gravadas como o `toISOString()` do JavaScript (`2026-10-12T18:41:00.000Z`, UTC), para o web ler sem conversão.

## 4. Arquitetura

```
NVDA
 └─ globalPlugins/NotasWorkflowNVDA/
     __init__.py        GlobalPlugin: atalhos, menu Ferramentas, painel de configurações, abre as janelas
     model.py           Raias, criação e validação de folhas, cadernos e pastas, filtros, datas ISO
     markup.py          Marcação leve <-> HTML do TipTap; HTML -> texto; formatação de seleção
     search.py          Normalização sem acentos, pontuação, trecho
     store.py           NotesStore: operações do web (lib/store.ts) + arquivo JSON (lib/storage.ts)
     messages.py        Textos traduzidos: nomes das raias, contagens, datas, descrição das folhas
     mainDialog.py      Janela "Notas Workflow NVDA": Mostrar, Visualização, árvore/tabela, ações
     noteDialog.py      Janelas "Nova folha" e da folha (editor)
     searchDialog.py    Janela "Buscar folhas"
     organizeDialog.py  Janela "Cadernos e pastas"
     settingsPanel.py   Configurações do NVDA > Notas Workflow NVDA
```

Camadas:

1. **Núcleo sem interface** (`model`, `markup`, `search`, `store`): não importa `wx` nem módulos do NVDA; é testado em Python 3.11 e 3.13.
2. **Interface** (`messages`, `mainDialog`, `noteDialog`, `searchDialog`, `organizeDialog`, `settingsPanel`): wxPython e `gui.guiHelper` do NVDA.
3. **Integração** (`__init__`): scripts, menu Ferramentas, registro do painel. Tudo roda na linha principal do NVDA (não há rede nem trabalho demorado: o arquivo é pequeno e local).

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
* Toda alteração grava na hora: escreve `NotasWorkflowNVDA-data.json.tmp`, guarda o arquivo anterior como `NotasWorkflowNVDA-data.json.bak` e troca com `os.replace` (atômico no Windows).
* Ao ler: arquivo ausente = nenhuma folha; JSON danificado ou acima de 20 MB = o arquivo é renomeado para `NotasWorkflowNVDA-data.corrupt-<data>.json` (nunca apagado), a cópia `.bak` é usada se estiver boa e a pessoa é avisada.
* Erro de gravação (disco cheio, pasta somente leitura): as folhas continuam na memória, a pessoa é avisada e a próxima alteração tenta de novo.
* Mudanças externas: o tamanho e a data do arquivo são lembrados; ao abrir a janela principal, se mudaram, o arquivo é lido de novo.

### 4.4 Busca (equivalente a `textSearch` e `extractExcerpt`)

1. A busca e o texto da folha (título, conteúdo sem marcação e tags) são normalizados: minúsculas (`casefold`) e sem acentos (NFKD sem marcas).
2. Pontuação = termos encontrados ÷ termos da busca (igual ao web). Desempate: termos encontrados no título, depois a folha alterada por último.
3. Trecho: até 120 caracteres em volta do primeiro termo encontrado, com "…" nas pontas (igual ao web, mas achando o termo sem acento).
4. Resultados com pontuação zero não aparecem; no máximo 100.

### 4.5 Erros

| Situação | Fala (pt_BR) |
|---|---|
| Arquivo danificado | As folhas salvas estavam danificadas. O arquivo foi guardado como <nome> e a cópia de segurança foi usada. |
| Não foi possível gravar | Não foi possível salvar as folhas em <pasta>. Confira se a pasta existe e pode ser gravada. |
| Importação inválida | Este arquivo não tem folhas do Notas Workflow NVDA. |
| Arquivo grande demais | O arquivo tem mais de 20 MB e não foi aberto. |
| Título vazio | O botão Criar folha fica indisponível até haver título |
| Folha excluída enquanto aberta | Esta folha foi excluída. |

## 5. Interface

### 5.1 Janela Notas Workflow NVDA (NVDA+Alt+N ou Ferramentas > Notas Workflow NVDA…)

Ordem de tabulação:

1. **Mostrar** (caixa): Todas as folhas, Folhas soltas, Folhas recentes, Caderno: <nome>…, Pasta: <nome>…
2. **Visualização** (caixa): Raias (árvore) ou Tabela; a escolha fica lembrada.
3. **Folhas** (árvore ou tabela; o rótulo diz o filtro e quantas folhas há).
   * Árvore: ramos "A fazer, 2 folhas"… já abertos; cada folha: "Título, caderno Trabalho, tags x, y, atualizada em 12/10/2026".
   * Tabela: colunas Título, Status, Caderno, Tags, Atualizada em.
   * Enter abre, Delete exclui, Alt+Shift+Seta para a direita/esquerda move para a raia seguinte/anterior.
4. Botões: **Nova folha…** (na raia selecionada), **Abrir**, **Mover para…**, **Mudar caderno…**, **Excluir**, **Buscar…**, **Cadernos e pastas…**, **Fechar** (Esc).

A janela é única: abrir de novo traz a mesma janela para a frente.

### 5.2 Nova folha (NVDA+Alt+F)

**Título** (obrigatório), **Caderno** (Folha solta ou um caderno), **Status** (as 4 raias), **Criar folha** (padrão; indisponível sem título) e **Cancelar**. Enter cria; Esc cancela. Depois de criar, a janela da folha abre com o foco no conteúdo.

### 5.3 Janela da folha (editor)

Título da janela = título da folha. Ordem: **Título**, **Caderno**, **Status**, **Tags (separadas por vírgula)**, **Conteúdo** (várias linhas), **Formatação…**, **Situação do salvamento** (somente leitura: "Salvo às 14:32", "Alterações não salvas…"), **Salvar e fechar**. Esc também salva e fecha. Ctrl+S salva sem fechar; Ctrl+B e Ctrl+I formatam no conteúdo.

### 5.4 Buscar folhas (NVDA+Alt+B)

**Buscar** (campo; busca 300 ms depois de parar de digitar, ou com Enter), **Resultados** (tabela: Título, Trecho, Relevância, Atualizada em; Enter abre), **Abrir**, **Fechar**. O NVDA fala "N resultados" ou "Nenhuma folha encontrada".

### 5.5 Cadernos e pastas

**Organização** (árvore: cada pasta com os seus cadernos; ramo "Sem pasta" com os cadernos soltos; cada caderno diz quantas folhas tem), **Novo caderno…**, **Nova pasta…**, **Renomear…**, **Mover para pasta…**, **Excluir**, **Fechar**.

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
