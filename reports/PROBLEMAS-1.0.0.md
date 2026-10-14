# Problemas encontrados na versão 1.0.0

Encontrados durante a construção e os testes, antes de gerar a versão. Todos corrigidos; a versão só foi gerada com 0 falhas.

## Problemas do complemento (P)

| ID | Teste | Gravidade | Causa | Correção |
|---|---|---|---|---|
| P-01 | test_pure: FUN-13 web formats | Média | `parseData` recusava `{"notes": {id: folha}}` (o formato do estado Zustand do web): a verificação de "há listas" rodava antes de converter o objeto em lista | Conversão feita antes da verificação |
| P-02 | test_gui: fim da suíte | Baixa | Ao destruir a janela principal, a árvore ainda enviava "seleção mudou" e o tratador usava controles já destruídos (`RuntimeError` no log) | `NotesDialog.destroy()` marca a janela como fechando; `updateButtons` não faz nada nesse estado |
| P-03 | test_accessibility: ACE-03 janela da folha | Média | O campo somente leitura "Situação do salvamento" de uma linha ficava fora da tabulação (no wx, `TextCtrl` de uma linha só entra no Tab se for editável) | Campo multilinha somente leitura, como o de situação do SpotifyNVDA |
| P-04 | test_security: SEG-05 JSON aninhado | Alta | Um arquivo com 100.000 listas aninhadas gerava `RecursionError`, que não era tratado: a importação derrubava o tratador do botão e um arquivo de dados assim não seria guardado à parte | `_readJson` transforma `RecursionError` em erro de arquivo inválido; o arquivo de dados é tratado como danificado (novo teste FUN-17) |
| P-05 | test_security: SEG-12 bandit | Baixa | Dois `except: pass` sem registro no `terminate` (B110) | Registram `log.debugWarning` |
| P-06 | Revisão do roteiro manual (MAN-18) | Média | Encerrar o NVDA com a janela de uma folha aberta, antes do salvamento automático, perderia o que foi digitado nos últimos segundos | O plugin lembra a janela aberta e o `terminate` salva o pendente; novo teste FUN-16 |

## Problemas do manual (D)

| ID | Teste | Causa | Correção |
|---|---|---|---|
| D-01 | test_manual: DOC-05 títulos | Os capítulos (`##` do MANUAL.md) saíam como Título 2 do Word, porque o `#` virava Título 1 só para a capa; navegar por cabeçalhos de nível 1 no leitor de telas não encontrava os capítulos | `#` vira o título da capa, `##` Título 1 e `###` Título 2 |

## Problemas dos testes (T)

| ID | Teste | Causa | Correção |
|---|---|---|---|
| T-01 | test_gui: FUN-06 tabela | Esperava as linhas na ordem de criação, mas a tabela segue a ordem das raias (como o quadro do web) | Expectativa corrigida |
| T-02 | test_gui: FUN-03 salvamento automático | Sem um laço de eventos ativo, `wx.Yield` não entrega eventos de temporizador; no NVDA o laço principal sempre existe | `_guiapp.py` ativa um `wx.GUIEventLoop` |
| T-03 | test_gui: `fakeModal` | Devolvia à classe os métodos herdados do wx (`IsModal`), que o sip não liga de novo à instância (`TypeError`) | Métodos herdados são removidos em vez de recolocados |
| T-04 | test_accessibility: ACE-04 botão padrão | A leitura MSAA passa o foco por todos os botões, e o botão focado vira o padrão temporário (Cancelar) | O teste devolve o foco ao título, onde a pessoa digita, antes de conferir; compara pelo ID |
