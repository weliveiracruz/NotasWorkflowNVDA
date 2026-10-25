# Problemas encontrados na versão 1.8.0

Versão da folha a partir de documento (Criar > Folha a partir de documento… e botão Inserir documento… da janela da folha, novo módulo `importer.py`: Word .docx, PowerPoint .pptx, texto, HTML e e-mail .eml; .doc, .ppt, .rtf, .pdf e .msg ficam de fora por decisão da pessoa responsável) e do Novo caderno com a escolha da pasta (`prompts.NotebookDialog`).

## Problemas do complemento (P)

| ID | Onde | Causa | Correção |
|---|---|---|---|
| P-01 | Leitura de documentos | Negrito e itálico juntos viravam `***texto***`, que o editor transforma em HTML com as marcas cruzadas (`<strong><em>x</strong></em>`) | Quando os dois vêm juntos, fica só o negrito |
| P-02 | Página HTML salva pelo Word | Cada parágrafo vinha separado por uma linha em branco (folha cheia de parágrafos vazios) e os marcadores da lista vinham como o caractere "·" | Linhas em branco não vêm para a folha; uma linha que começa com •, ·, ▪ ou o marcador do Word vira item de lista |
| P-03 | Janela da folha | O temporizador do salvamento automático não era parado quando a janela era destruída sem passar por Salvar e fechar | A janela para o temporizador no evento de destruição (`onDestroy`) |

## Problemas dos testes (T)

| ID | Teste | Causa | Correção |
|---|---|---|---|
| T-01 | test_gui (FUN-34) | Ao rodar depois de `run()`, o processo de teste caía com "access violation" dentro do laço de eventos do wx. O mesmo acontece na 1.7.0: basta processar eventos por cerca de dois segundos depois de `run()` (antes, nenhum teste fazia isso). Não é causado pelo código novo nem pelas janelas que os testes deixam abertas (destruí-las ou parar seus temporizadores não muda nada) | Os testes de documentos rodam antes de `run()`. A causa exata dentro de `run()` fica para investigar; não foi vista no NVDA |
| T-02 | test_accessibility: ACE-02 do menu Criar | O teste esperava exatamente três itens no menu Criar | O teste confere os quatro itens e as letras de atalho distintas |
| T-03 | test_security: SEG-01, SEG-03 e SEG-12 | Os nomes fixos de XML do Word e do PowerPoint também estão em `importer.py`; os módulos `email`, `io`, `posixpath` e `xml` da biblioteca padrão não estavam na lista; o bandit aponta o uso do ElementTree | Lista e regra ajustadas (os módulos existem no Python do NVDA, conferido em FUN-16); o importador recusa qualquer DTD antes de ler o XML (SEG-13), anotado com `nosec` |
