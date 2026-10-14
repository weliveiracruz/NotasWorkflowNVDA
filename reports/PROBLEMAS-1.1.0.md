# Problemas encontrados na versão 1.1.0

Versão de troca de nome (NotasWorkflow para Notas Workflow NVDA) com migração dos dados.

Nenhum problema encontrado: todas as suítes passaram na primeira execução completa (nº 5), com os casos novos FUN-20 e SEG-11.

## Pendências conhecidas (não são falhas desta versão)

| ID | Situação | Encaminhamento |
|---|---|---|
| PEND-01 | Busca lenta com muitas folhas: cerca de 3 s com 10 mil, 23 s com 20 mil e de 34 a 92 s com 100 mil (massas de `tests/gerar_massa.py`) | Guardar o texto já preparado de cada folha; aguardando aprovação |
| PEND-02 | O limite de 20 MB vale também para o próprio arquivo de dados (cerca de 28 mil folhas), mas a gravação não o respeita | Aumentar o limite e nunca recusar o próprio arquivo pelo tamanho; aguardando aprovação |
