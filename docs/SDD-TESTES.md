# SDD de testes do Notas Workflow NVDA

Especificação dos testes do complemento NotasWorkflowNVDA: **o que** é testado, **como** e **quando**. Vale para todas as versões a partir da 1.0.0. Complementa a seção 8 do [SDD.md](SDD.md).

## 1. Objetivo

Garantir, a cada nova versão, que o NotasWorkflowNVDA:

1. **funciona** como o Notas Workflow web: folhas, raias, cadernos, pastas, edição, salvamento, busca, importação e exportação (prefixo FUN);
2. **é acessível** para quem usa o NVDA (prefixo ACE);
3. **não expõe nem perde** as folhas da pessoa (prefixo SEG);
4. tem o **manual de uso** (HTML dentro do pacote, aberto pelo botão Manual de uso…) atualizado e completo (prefixo DOC).

## 2. Ambiente de teste

| Item | Como é feito |
|---|---|
| Interface | wxPython real (a mesma biblioteca do NVDA), janelas reais do Windows, com laço de eventos ativo para os temporizadores (salvamento automático, busca enquanto digita) |
| NVDA | Módulos simulados (`tests/nvda_stubs.py`), exceto o `gui.guiHelper`, que é o arquivo original do NVDA |
| Entrada de fora | Toda entrada real de teclado e mouse nas janelas dos testes é descartada (`_TestApp.FilterEvent`): elas são reais e podem pegar o primeiro plano enquanto alguém usa o computador, e uma tecla digitada em outro lugar mudaria a seleção pela busca por digitação da árvore |
| Teclado | As teclas vão direto para quem as trata (`handleTreeKey`). Com `NOTASWORKFLOWNVDA_REALKEYS=1`, vão como mensagens reais do Windows; esse caminho depende de quem está em primeiro plano na área de trabalho e por isso não é o padrão (o Enter real fica no roteiro manual, MAN-26) |
| Janelas modais e menus | `ShowModal`, os menus (Mover para, Formatação) e as caixas de escolha são trocados por ações do teste (`tests/_guiapp.py`), sem mudar o código do complemento |
| Leitor de telas | No Windows, os nomes dos controles e dos itens da árvore são lidos pelo MSAA (`oleacc`), a mesma interface que o NVDA usa nesses controles |
| Arquivos | Pastas temporárias novas a cada teste; arquivos danificados, gigantes (esparsos), aninhados e hostis criados pelos testes |
| NVDA instalado | `tests/test_nvda_runtime.py` confere o `library.zip` do NVDA instalado |
| Python | 3.11 (NVDA 2024.1 a 2025.x) e 3.13 (NVDA 2026.x) |
| Análise estática | `bandit` (nenhum aviso, nem baixo) e varredura de padrões proibidos |

## 3. Suítes

| Suíte | Arquivo | Tipo |
|---|---|---|
| Unidades | `tests/test_pure.py` (via `_run_unittest.py`) | FUN |
| Interface | `tests/test_gui.py` | FUN |
| Acessibilidade (inglês e português) | `tests/test_accessibility.py` | ACE |
| Tradução | `tests/test_translation.py` | ACE |
| Segurança | `tests/test_security.py` | SEG |
| NVDA instalado | `tests/test_nvda_runtime.py` | FUN |
| Pacote | `tests/run_all.py` (etapa build) | FUN |
| Desempenho (100 mil folhas) | `tests/test_performance.py` | PERF |
| Manual | `tests/test_manual.py` (depois do build) | DOC |

`python tests/run_all.py --note "o que mudou"` roda tudo, grava o histórico em `reports/execucoes.json` e o resumo em `reports/ULTIMA-EXECUCAO.md`.

## 4. Casos funcionais (FUN)

| ID | Caso | Resultado esperado | Suíte |
|---|---|---|---|
| FUN-01 | Criar folha | Mesmos campos e padrões do web (A fazer, sem caderno, `createdAt` = `updatedAt`); raia e caderno escolhidos; raia e caderno inválidos recusados; título limpo e limitado; IDs uuid4 únicos; título vazio deixa Criar folha indisponível; cancelar não cria; nova folha nasce na raia selecionada | pure, gui |
| FUN-02 | Editar folha | `updatedAt` só muda quando algo muda; tags limpas, sem repetição, limitadas; conteúdo limitado; janela mostra a folha; título da janela acompanha; folha excluída enquanto aberta é avisada e não volta; HTML do web mantido quando só o título muda | pure, gui |
| FUN-03 | Salvamento automático | "Alterações não salvas…" ao digitar; salva sozinho depois do intervalo; situação diz a hora; anuncia só se configurado; Ctrl+S salva na hora; fechar, Esc e Salvar e fechar salvam o pendente | gui |
| FUN-04 | Formatação | Negrito, itálico, tachado, código (envolve, desfaz e cursor entre as marcas); título 2/3, listas, citação (linha atual ou linhas selecionadas, alterna); divisor em linha própria; Ctrl+B/I no conteúdo; menu Formatação…; seleção mantida no texto formatado; opções iguais às da barra do web | pure, gui |
| FUN-05 | Marcação ↔ HTML do TipTap | Ida e volta sem perda; HTML igual ao do TipTap (`<li><p>`, `<ol start>`); HTML do web (`<b>`, `<i>`, `<br>`, listas aninhadas, `<pre>`) lido; marcas desconhecidas viram texto; entidades; texto puro; HTML quebrado não derruba; árvore mostra raia, título, caderno e data | pure, gui |
| FUN-06 | Raias e tabela | 4 raias do web com as mesmas cores; vizinhas; ordem de criação mantida; tabela com Título, Status, Caderno, Tags e Atualizada em; visualização lembrada; Enter na tabela abre | pure, gui |
| FUN-07 | Mover entre raias | Alt+Shift+Seta para a direita/esquerda; aviso nas pontas; Mover para… com as outras raias; cancelar não muda; a seleção acompanha a folha; setas comuns continuam funcionando | pure, gui |
| FUN-08 | Mudar caderno | Mudar caderno… move para um caderno ou de volta a folha solta, com aviso | gui |
| FUN-09 | Excluir folha | Pergunta; Não mantém; Sim exclui, anuncia e seleciona a vizinha | pure, gui |
| FUN-10 | Filtros | Todas, soltas, recentes (10 alteradas por último), por caderno e por pasta (folhas da pasta e dos cadernos dela); rótulo diz o filtro e a quantidade; filtros acompanham cadernos e pastas criados, renomeados e excluídos | pure, gui |
| FUN-11 | Busca | Sem acentos e maiúsculas; pontuação = termos encontrados ÷ termos; desempate pelo título; tags; marcação não é buscada; trecho como o do web; limite de 100; busca enquanto digita; relevância em %; anúncio do número de resultados ou de nada encontrado; Abrir | pure, gui |
| FUN-12 | Cadernos e pastas | Cores em rodízio do web; excluir caderno solta as folhas; excluir pasta solta cadernos e folhas; renomear; mover caderno; nome vazio recusado; janela com pastas, cadernos e "Sem pasta"; novo caderno dentro da pasta selecionada | pure, gui |
| FUN-13 | Importar e exportar | Exportar e importar em outra pasta; formatos do web (lista, `{notes}`, `{notes: {id: nota}}` do Zustand, chaves do `localStorage`); versão mais nova vence; arquivos inválidos explicados | pure, gui |
| FUN-14 | Janela principal | Menu Ferramentas; NVDA+Alt+N; janela reaproveitada; botões indisponíveis sem folha | gui |
| FUN-15 | Configurações e pasta | Mostra a pasta em uso; salva intervalo e anúncio; pasta vazia recebe a cópia; pasta com folhas passa a ser usada; pasta inexistente recusada; Procurar; pasta padrão; falha de cópia mantém a pasta antiga | pure, gui |
| FUN-16 | NVDA real, Python e encerrar | Todo módulo e função usados existem no NVDA instalado; manifesto aceito; todo arquivo compila em 3.11 e 3.13; encerrar fecha a janela e remove o painel sem erros no log | runtime, pure, gui |
| FUN-17 | Arquivo | Arquivo ausente = vazio; tudo salvo e lido; `.bak` com a versão anterior; sem `.tmp` sobrando; arquivo danificado (ou aninhado demais) guardado com outro nome e cópia usada, com aviso falado; itens inválidos descartados; erro de gravação avisado com a pasta; mudança feita por outro programa lida de novo ao abrir a janela; BOM aceito | pure, gui |
| FUN-18 | Comandos | NVDA+Alt+F cria folha; NVDA+Alt+B abre a busca; resumo das raias | gui |
| FUN-21 | Mover para caderno ou pasta (1.2.0) | Caderno, direto numa pasta ou solta; caderno vence; lugares desconhecidos viram solta; folhas por caderno, por pasta e soltas; Mover para começa no lugar atual e escolher o mesmo lugar não muda nada; anúncio "Agora em: …" | pure, gui |
| FUN-22 | Índice e busca preparada (1.2.0) | `getNote` pelo índice acompanha inclusões, exclusões e listas novas; importação que substitui folha atualiza o índice; texto da busca reaproveitado e refeito quando a folha muda; texto sem marcação, scripts e estilos; arquivo compacto; limite de 200 MB | pure, gui |
| FUN-23 | Enter abre a folha (1.2.0) | Enter (pelo tratador de teclas; como mensagem real do Windows com `NOTASWORKFLOWNVDA_REALKEYS=1`) abre a folha selecionada na lista e na árvore de Cadernos e pastas; Enter e clique duplo juntos abrem uma vez só; Enter numa raia abre e fecha a raia | gui |
| FUN-24 | Listas paginadas (1.2.0) | Uma raia longa mostra uma página e "Mostrar mais" com o número restante; Enter nele mostra a próxima página com o foco na primeira nova; selecionar uma folha além da página mostra a página dela; o mesmo num caderno com muitas folhas | gui |
| FUN-25 | Raias fechadas (1.3.0) | As raias começam fechadas, com o número de folhas; sem folha a selecionar, o foco fica na primeira raia; selecionar uma folha abre só a raia dela; as raias ficam como a pessoa as deixou quando a lista é refeita | gui |
| FUN-26 | Pilha da raia (1.3.0) | Status mudado na janela da folha: ao fechar, o foco vai para a próxima folha da raia; última folha: a anterior; única: a raia; folha só editada: o foco volta para ela; folha que sai do filtro pelo Local: a próxima da raia | gui |
| FUN-27 | Exportar como documento (1.4.0) | Botão Exportar… com menu Folha selecionada (só com folha), Caderno e Pasta; caderno e pasta do filtro ou da folha já escolhidos; folha pergunta só o formato; caderno e pasta perguntam um arquivo ou um por folha; nome sugerido e extensão acrescentada; Word, Markdown e HTML com título do documento, títulos por nível (conteúdo abaixo da folha), Status, Local, Tags, datas, negrito, itálico, tachado, código, listas (numerada recomeça e respeita o início), citação, bloco de código e divisor; Markdown escapa o que viraria lista, título ou citação; .docx válido, com estilos de título, idioma e título nas propriedades, igual para as mesmas folhas; um arquivo por folha em pasta nova, subpasta por caderno, nomes limpos e repetidos numerados, nada sobrescrito; caderno vazio, sem cadernos, cancelar e falha de gravação falados sem gravar nada; caracteres inválidos em XML descartados | pure, gui |
| FUN-28 | Campo Local em árvore (1.5.0) | Nova folha, janela da folha e Mover para mostram a árvore: Folha solta, cada pasta com o número de cadernos e os cadernos dela dentro, os cadernos sem pasta; pastas começam fechadas e só abre a pasta do local escolhido; a própria pasta é um local (folha direto na pasta); Enter na árvore cria a folha (Nova folha) ou move (Mover para); na janela da folha, o local atual vem escolhido sem nada a salvar, escolher outro é uma mudança salva ao fechar; Mover para começa no local atual, o título da janela diz a folha, Cancelar mantém o local | gui |
| FUN-29 | Manual de uso (1.5.0) | Botão Manual de uso… na janela principal e comando sem atalho abrem o manual inteiro (em português, com títulos e tabelas) na janela de leitura do NVDA (`ui.browseableMessage` com HTML); manual ausente: o NVDA fala e nada abre | gui |
| FUN-30 | Ordem na raia (1.6.0) | `placeNoteBeside` põe antes ou depois da vizinha, só muda a ordem (outras raias e `updatedAt` iguais), já no lugar ou ela mesma não muda nada, folha desconhecida é erro, ordem gravada no arquivo; Ctrl+Shift+Seta para cima/baixo sobem e descem com a seleção acompanhando e "Posição n de total"; topo e fim falados sem mudar; a ordem continua depois de refazer a árvore; num caderno passa a vizinha mostrada; Folhas recentes avisa e não muda; numa raia nada muda; no fim de uma página passa a primeira folha ainda não mostrada | pure, gui |
| FUN-20 | Novo nome (1.1.0) | Arquivo antigo da pasta copiado para o nome novo e nunca alterado; o novo vence e a cópia é feita uma vez; primeiro início traz folhas, cópia de segurança e configurações do NotasWorkflow 1.0.0, com aviso falado; nada do antigo muda | pure, gui |
| FUN-19 | Datas | Formato do `toISOString()` do JavaScript; datas inválidas recusadas | pure |

## 5. Casos de acessibilidade (ACE)

| ID | Caso | Resultado esperado |
|---|---|---|
| ACE-01 | Nomes | Todo controle que recebe foco tem nome, conferido também pelo MSAA, em todas as janelas (principal em árvore e em tabela, Nova folha, folha, Buscar, Cadernos e pastas, Configurações) |
| ACE-02 | Letras de atalho | Únicas em cada janela; todo botão e rótulo tem uma; mantidas na tradução |
| ACE-03 | Ordem de tabulação | Principal: Mostrar, Folhas, ações, Buscar, Cadernos e pastas, Exportar (1.4.0), Manual de uso (1.5.0), Fechar; Nova folha; folha; Buscar; Mover para (1.5.0): árvore Local, OK, Cancelar, com o foco na árvore; a tabela substitui a árvore |
| ACE-04 | Botões indisponíveis | Fora da tabulação quando não servem (sem folha; "Sem pasta"; Criar folha sem título); Criar folha é o botão padrão (Enter cria) |
| ACE-05 | Teclado | Esc fecha (e salva na folha); Alt+Shift+Setas movem; Enter abre e busca |
| ACE-06 | Foco | Começa nas folhas, no título (Nova folha e abrir folha), no conteúdo (folha recém-criada), no campo de busca e na árvore de cadernos; fica na folha movida; vai para a vizinha depois de excluir; Enter na busca vai aos resultados |
| ACE-07 | Fala | Mover, formatar, criar, excluir e buscar são anunciados |
| ACE-08 | Títulos | Toda janela tem título; a janela da folha tem o título da folha; Mover para diz a folha no título (1.5.0); o painel tem categoria |
| ACE-09 | Atalhos padrão | Três (NVDA+Alt+N, F, B), sem conflito com o NVDA instalado e com os outros complementos instalados |
| ACE-10 | Comandos | Todos com descrição, na categoria Notas Workflow NVDA |
| ACE-12 | Tradutores | Todo texto traduzível tem comentário `# Translators:` |
| ACE-13 | Situação do salvamento | Somente leitura e alcançável com Tab |
| ACE-14 | Rótulo da lista | Diz o filtro e a quantidade, também pelo MSAA; `&` em nome de caderno é lido como "&" e não vira letra de atalho; a árvore Local (1.5.0) tem o nome "Local", também pelo MSAA |
| ACE-16 | Documentação | HTML com idioma, cabeçalhos e tabelas de verdade, em inglês e português |
| ACE-17 | Tradução | Toda frase traduzida, sem vazias nem obsoletas, mesmos `{marcadores}`, "…" mantido, nomes das raias iguais aos do web, manifesto e documentação em pt_BR com todos os atalhos |
| ACE-18 | Árvore pelo MSAA | Folha lida com título, caderno, tags e data; raia lida com nome, número de folhas e "expandido"; pasta da árvore Local (1.5.0) lida com o nome, o número de cadernos e "recolhido" |
| ACE-19 | Cor | A raia é sempre dita pelo nome (nunca só pela cor); a tabela tem a coluna Status |

## 6. Casos de vulnerabilidade e privacidade (SEG)

| ID | Caso | Resultado esperado |
|---|---|---|
| SEG-01 | Sem rede | Nenhum módulo de rede importado; nenhum endereço web no código (os únicos endereços são os nomes fixos de XML que todo documento do Word declara, só em `exporter.py`, nunca abertos); usar o complemento (criar, buscar, abrir, exportar, importar) não abre nenhuma conexão (`socket` bloqueado no teste) |
| SEG-02 | Log | Títulos, conteúdos e tags nunca vão para o log, nem em erros de gravação, arquivo danificado ou importação inválida; erros registrados só pelo tipo; detalhe limitado a 200 caracteres |
| SEG-03 | Código perigoso | Nenhum `eval`, `exec`, `pickle`, `marshal`, `subprocess`, shell ou `ctypes`; só biblioteca padrão (incluindo `zipfile` para o .docx) e NVDA |
| SEG-04 | Tamanho | Importação acima de 20 MB recusada **sem abrir** o arquivo; arquivo de dados acima de 20 MB não carregado e guardado à parte (nunca apagado) |
| SEG-05 | Dados não confiáveis | IDs com caracteres de caminho recusados; nomes, títulos, conteúdo e tags limitados; cores validadas; raia desconhecida trocada; referências inexistentes removidas; campos desconhecidos descartados; tipos errados viram vazios; JSON aninhado demais e arquivo binário recusados sem derrubar o NVDA |
| SEG-06 | HTML | O que a pessoa digita é escapado; HTML de arquivos perde scripts, estilos, quadros e atributos; o complemento nunca exibe HTML; o HTML exportado (1.4.0) só tem as tags dos formatos do editor, sem scripts, quadros, links, imagens ou atributos vindos das folhas, com títulos e textos escapados |
| SEG-07 | Gravação atômica | Falha de gravação é avisada e deixa o arquivo salvo intacto, sem `.tmp`; `os.fsync` e `os.replace` |
| SEG-08 | Nomes de arquivo | Dados nunca decidem o nome do arquivo de dados; nada é gravado fora da pasta; exportação só com as folhas (sem configurações nem caminhos). Exportar um arquivo por folha (1.4.0): títulos com `..`, barras, unidades, nomes reservados (CON, NUL…), caracteres proibidos e nomes longos viram nomes limpos, e tudo fica dentro da pasta nova criada na pasta escolhida |
| SEG-09 | Confirmações | Excluir folha, caderno ou pasta sempre pergunta, com Não como padrão; qualquer resposta diferente de Sim mantém; excluir caderno nunca apaga folhas |
| SEG-10 | Telas seguras | Complemento desligado |
| SEG-11 | Desinstalar e migrar | Sem tarefa de desinstalação: as folhas ficam; a migração do NotasWorkflow 1.0.0 só copia (sem mover, renomear ou apagar); o único arquivo apagado é o temporário do próprio complemento |
| SEG-12 | Análise estática | bandit sem nenhum aviso (nem baixo) |

## 6.2 Casos de desempenho (PERF)

Com 100 mil folhas em 80 cadernos e 12 pastas, geradas por `tests/gerar_massa.py`. Cada operação é medida depois da gravação anterior terminar, como quando a pessoa espera a resposta. Os limites são folgados para uma máquina ocupada e muito abaixo do que fazia o NVDA parar de responder antes da 1.2.0.

| ID | Caso | Limite |
|---|---|---|
| PERF-01 | O complemento fica pronto ao iniciar o NVDA | 0,5 s |
| PERF-02 | As 100 mil folhas são lidas (em segundo plano) e todas ficam disponíveis | 20 s |
| PERF-03 | A janela abre durante a preparação da busca; reabrir é instantâneo | 3 s / 0,5 s |
| PERF-04 | A busca termina de ser preparada em segundo plano | 180 s |
| PERF-05 | Uma raia mostra uma página, não 25 mil itens | 201 itens |
| PERF-06 | Alt+Shift+Seta muda o status e a folha continua selecionada | 2 s |
| PERF-07 | Trocar o filtro para um caderno e voltar | 2 s |
| PERF-08 | Abrir, editar e fechar uma folha (grava e atualiza a lista) | 2 s |
| PERF-09 | Salvar não para o NVDA; a gravação em segundo plano termina | 0,1 s / 15 s |
| PERF-10 | Buscar o nome de um projeto, palavras comuns e nada | 2 s cada |
| PERF-11 | Abrir Cadernos e pastas, abrir um caderno com as folhas, reconstruir a árvore | 3 s / 2 s / 3 s |
| PERF-12 | Fechar a janela | 2 s |
| PERF-13 | Encerrar o NVDA com tudo gravado | 20 s |
| PERF-14 | Exportar a maior pasta (1.4.0) num arquivo Word e num Markdown por folha: a janela continua respondendo e a gravação termina em segundo plano | 1 s / 60 s |
| PERF-15 | Ctrl+Shift+Seta muda a folha de lugar na raia (1.6.0), com a folha continuando selecionada | 1 s |

## 6.1 Casos do manual de uso (DOC)

| ID | Caso | Resultado esperado |
|---|---|---|
| DOC-01 | Arquivo do manual (1.5.0) | `addon/doc/pt_BR/manual.html` existe, é HTML bem formado (todo elemento fechado na ordem) e o pacote da versão tem o mesmo arquivo; não existe mais manual em Word |
| DOC-02 | Atualizado | Gerado do `MANUAL.md` atual (SHA-256 num `meta`); da versão do manifesto; com linha da versão no histórico e versão no topo |
| DOC-03 | Completo | Todo botão, campo e menu com letra de atalho (tirados da tradução pt_BR), as 4 raias, os 10 formatos, as opções de Mostrar, Visualização e Situação do salvamento e as colunas das tabelas aparecem no manual |
| DOC-04 | Atalhos | Todo atalho padrão (lido dos scripts) e as teclas das janelas aparecem no manual |
| DOC-06 | Só este complemento | Manual, readmes, manifestos e textos da interface não citam outra plataforma |
| DOC-05 | Acessível | Idioma pt-BR e título; um só h1, capítulos em h2 e seções em h3; toda tabela com cabeçalho (`th scope="col"`); sumário com links para todos os capítulos; nenhum script, quadro, formulário, arquivo externo ou imagem |

## 7. Critérios de aprovação

* Uma versão só é gerada com **0 falhas** em todas as suítes (`build.py --release` recusa gerar o pacote se algo falhar).
* Falha de SEG ou ACE é sempre bloqueante.
* Cada problema encontrado vai para `reports/PROBLEMAS-<versão>.md`: problemas do complemento (P-xx) e dos testes (T-xx), com gravidade, causa e correção.

## 8. Fora da automação

Fala real do NVDA, pasta sincronizada com OneDrive/Google Drive em dois computadores e troca de arquivos com a aplicação web: roteiro em [TESTES-MANUAIS.md](TESTES-MANUAIS.md).
