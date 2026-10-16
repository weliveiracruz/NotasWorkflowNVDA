# Notas Workflow Mac

A versão para Mac do complemento **Notas Workflow NVDA**: folhas e tarefas em raias de status (A fazer, Em andamento, Bloqueada, Concluída), em cadernos e pastas, com tags, conteúdo formatado, salvamento automático e busca. Tudo pelo teclado, com as falas pelo **VoiceOver**, e rápido mesmo com dezenas de milhares de folhas.

É um app nativo (Swift e AppKit) para Mac com Apple Silicon (M1 a M4), macOS 13 ou mais novo. O fluxo, as janelas, os nomes dos botões e as falas são os mesmos do complemento 1.3.0.

## Mesmo arquivo do Windows

O app usa o mesmo arquivo do complemento, `NotasWorkflowNVDA-data.json`, no mesmo formato. Escolha nas Configurações dos dois uma pasta do OneDrive, do Google Drive ou do iCloud Drive e as mesmas folhas aparecem no Windows com o NVDA e no Mac com o VoiceOver. Quando o arquivo muda em outro computador, o app lê de novo ao abrir a janela.

## Como instalar

1. Instale as ferramentas de linha de comando da Apple (uma vez só): no Terminal, `xcode-select --install`. O Xcode não é necessário.
2. Na pasta do projeto, rode `./build-app.sh --instalar`. O script roda os autotestes, compila para arm64, monta o app, assina para uso local e copia para Aplicativos.
3. Abra **Notas Workflow Mac** em Aplicativos. Para ele abrir sozinho, marque **Abrir ao iniciar sessão** nas Configurações.

Sem `--instalar`, o app fica em `build/Notas Workflow Mac.app`.

## Atalhos

O NVDA usa NVDA+Alt; no Mac, Control+Option é a tecla do VoiceOver, então os atalhos globais usam **Option+Shift+Command**. Eles funcionam em qualquer app.

| Atalho | Ação |
|---|---|
| ⌥⇧⌘N | Abrir a janela do Notas Workflow (NVDA+Alt+N) |
| ⌥⇧⌘F | Nova folha (NVDA+Alt+F) |
| ⌥⇧⌘B | Buscar nas folhas (NVDA+Alt+B) |
| ⌥⇧⌘L | Dizer quantas folhas cada raia tem (no NVDA, sem atalho) |
| ⌥⇧ Seta para a direita e para a esquerda | Próximo ou anterior status da folha (Alt+Shift+Setas) |
| ⌘S, ⌘B, ⌘I | Salvar, negrito e itálico na janela da folha (Ctrl+S, B, I) |
| ⌘, | Configurações |

Nas janelas, como as letras de atalho do Windows não existem no Mac:

| Janela | Atalhos |
|---|---|
| Principal | ⌘N Criar…, ⌘U Atualizar o status da tarefa…, ⇧⌘M Mover para…, Delete ou ⌘Delete Excluir, ⌘F Buscar…, ⌘O Cadernos e pastas…, Esc ou ⌘W Fechar |
| Folha | ⇧⌘F Formatação…, ⌘S Salvar, ⌘Return ou Esc Salvar e fechar |
| Cadernos e pastas | ⌘N Criar…, ⌘R ou F2 Renomear…, ⇧⌘M Mover para…, Delete Excluir, Esc Fechar |
| Buscar | Return na lista ou ⌘O Abrir, Esc Fechar |

Com o VoiceOver, todos os botões e campos também são alcançados com VO+Setas. Para o Tab passar por todos os botões, ative em Ajustes do Sistema, Teclado, **Navegação pelo teclado**.

## A janela principal

**Mostrar**: todas as folhas, folhas soltas, folhas recentes (as 10 alteradas por último), um caderno ou uma pasta.

**Folhas**: as raias em árvore ("A fazer, 3 folhas"). As raias começam fechadas: Seta para a direita abre, Seta para a esquerda fecha. Return abre a folha, Delete exclui (depois de confirmar), ⌥⇧ Setas mudam o status. Cada raia mostra 200 folhas por vez; "Mostrar mais folhas" no fim mostra as próximas.

Botões: **Criar…** (folha, caderno ou pasta), **Atualizar o status da tarefa…**, **Mover para…** (caderno, direto para uma pasta, ou solta), **Excluir**, **Buscar…**, **Cadernos e pastas…** e **Fechar**. Fechar só esconde a janela: o app continua aberto para os atalhos, como o complemento dentro do NVDA.

## Folhas

**Criar… > Folha…** (ou ⌥⇧⌘F) pergunta o título, o local e o status, e abre a janela da folha: título, local, status, tags (separadas por vírgula) e conteúdo. Ao mudar o status ou o local e fechar a janela, o foco vai para a próxima folha da mesma raia. A folha se salva sozinha 2 segundos depois de você parar de digitar; ⌘S salva na hora, e fechar a janela sempre salva.

O conteúdo usa a mesma marcação leve do complemento:

| Digite | Para ter |
|---|---|
| `## Título` ou `### Título` | Título 2 ou 3 |
| `- item` | Lista com marcadores |
| `1. item` | Lista numerada |
| `> texto` | Citação |
| `---` | Divisor |
| `**texto**` | Negrito (⌘B) |
| `*texto*` | Itálico (⌘I) |
| `~~texto~~` | Tachado |
| `` `texto` `` | Código |

O botão **Formatação…** tem todos os formatos; aplica ao texto selecionado ou à linha atual, e escolher de novo remove.

## Busca, cadernos e pastas

**Buscar** procura no título, no conteúdo e nas tags, sem diferenciar acentos e maiúsculas, enquanto você digita. Os resultados mostram título, trecho, relevância e data; Return abre a folha.

**Cadernos e pastas** mostra cada pasta com os cadernos e as folhas, "Sem pasta" e "Folhas soltas". Excluir um caderno ou uma pasta nunca apaga folhas: elas ficam soltas.

## Onde ficam as folhas

Por padrão em `~/Library/Application Support/NotasWorkflowMac/NotasWorkflowNVDA-data.json`. As Configurações (⌘,) mudam a pasta, o tempo do salvamento automático, o anúncio do salvamento, e têm **Importar folhas…** e **Exportar folhas…**. A gravação é segura: a versão anterior fica em `.bak`, um arquivo danificado é guardado com outro nome e a cópia de segurança é usada, e tudo o que estiver pendente é gravado antes de o app fechar.

O app não usa a internet.

## Diferenças em relação ao complemento do NVDA

* Falas pelo VoiceOver (anúncios) no lugar do NVDA; atalhos globais com ⌥⇧⌘ no lugar de NVDA+Alt.
* As Configurações ficam no próprio app (⌘,), e não nas Configurações do NVDA; há também **Abrir ao iniciar sessão**.
* "Salvar automaticamente depois de" é uma lista de 1 a 30 segundos.
* O app fica no Dock e na barra de menus, com os mesmos comandos do item do menu Ferramentas do NVDA.
* Os textos seguem o idioma do Mac: português ou inglês.

## Para quem desenvolve

* `Sources/NotasCore`: modelo, arquivo, marcação e busca, sem AppKit (porte de `model.py`, `store.py`, `markup.py` e `search.py`). Mudou o formato no complemento, mude aqui também.
* `Sources/NotasWorkflowMac`: janelas, atalhos globais e VoiceOver.
* `Sources/NotasSelfTest`: autotestes com os casos de `tests/test_pure.py`, inclusive 100 mil folhas. `swift run NotasSelfTest`.
* `Sources/NotasWorkflowMac/Translations.swift` é gerado do `nvda.po` do complemento: `python3 tools/gerar_traducoes.py <caminho do nvda.po>`.

Licença: GNU GPL versão 2 (`COPYING.txt`).
