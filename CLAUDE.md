# Instruções para quem trabalha neste repositório (pessoas e agentes de IA)

O NotasWorkflowNVDA é o complemento do NVDA equivalente à aplicação web Notas Workflow (`C:\git\notasworkflow`). O modelo de dados (`model.py`, `store.py`) segue `types/index.ts` e `lib/store.ts` do web: mudou lá, mude aqui e nos testes (`docs/SDD.md`, seção 2).

## Regra obrigatória: testes a cada nova versão

Toda nova versão (toda mudança no campo `version` de `addon/manifest.ini`) **precisa** passar por todos os testes antes de ser gerada (`docs/SDD.md`, seção 9, e `docs/SDD-TESTES.md`):

1. Atualize `version` e `changelog` em `addon/manifest.ini` e `addon/locale/pt_BR/manifest.ini`, e o `CHANGELOG.md`.
2. Atualize o **manual de uso em Word**: edite `docs/manual/MANUAL.md` (a fonte) descrevendo a funcionalidade nova ou alterada, os nomes de botões e campos em português com a letra de atalho, o que o NVDA fala e as teclas; acrescente uma linha da versão em "Histórico deste manual". O `build.py` gera `docs/Manual-NotasWorkflowNVDA.docx` (ou rode `python docs/manual/gerar_manual.py`). Nunca edite o `.docx` à mão. A suíte `tests/test_manual.py` recusa a versão se algum botão, campo, menu, raia, formato ou atalho não estiver no manual, ou se o `.docx` estiver desatualizado.
3. Escreva ou atualize os testes das funções novas ou alteradas (funcionais em `tests/test_pure.py` ou `tests/test_gui.py`, acessibilidade em `tests/test_accessibility.py`, vulnerabilidade em `tests/test_security.py`) e acrescente os casos no `docs/SDD-TESTES.md`.
4. Rode todas as suítes: `python tests/run_all.py --note "o que mudou"` (precisa de `pip install wxPython bandit comtypes`; Python 3.11 e 3.13).
5. Se algo falhar: registre em `reports/PROBLEMAS-<versão>.md` (P-xx do complemento, T-xx dos testes), corrija e rode de novo até **0 falhas**.
6. Gere `reports/RELATORIO-TESTES-<versão>.md` com os números de `reports/execucoes.json`.
7. Gere o pacote só com `python build.py --release`: ele roda tudo de novo e **recusa** gerar o pacote se algum teste falhar.

Isso vale para **toda** alteração de comportamento ou de interface, mesmo sem versão nova: o manual em Word precisa sempre descrever o complemento como ele está.

Nunca apague nem edite à mão execuções antigas em `reports/execucoes.json`.

## Outras regras

* Só biblioteca padrão do Python e módulos do NVDA; nenhum módulo de rede (o complemento não usa a internet).
* `model`, `markup`, `search` e `store` não importam `wx` nem módulos do NVDA.
* Indentação com tabulação, como no NVDA.
* Todo texto da interface passa por `_()`, com `# Translators:` na linha anterior, e é traduzido em `addon/locale/pt_BR/LC_MESSAGES/nvda.po`.
* Letras de atalho (&) únicas em cada janela, em inglês e em português.
* Nunca registrar título, conteúdo ou tags das folhas no log.
* Nunca apagar folhas do usuário: excluir caderno ou pasta solta as folhas; desinstalar não apaga nada.
