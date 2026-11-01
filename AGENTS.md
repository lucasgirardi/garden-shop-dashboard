# AGENTS.md: Instruções para agentes de IA

> Projeto de **Lucas Girardi**: Garden Shop, dashboard de estoque e reposição (Python + Streamlit).

## 1. Objetivo

Este documento define as regras que agentes de IA (e pessoas) devem seguir ao analisar, planejar, implementar, testar e documentar alterações neste repositório.

## 2. Hierarquia de referência

Antes de iniciar uma tarefa:

1. Leia este `AGENTS.md` inteiro.
2. Leia o `PRD.md` para entender o problema, os usuários, o escopo, as regras de negócio (`RN-001` a `RN-011`) e os cenários de aceitação (`CA-001` a `CA-011`).
3. Leia a `SPEC.md` para identificar os requisitos técnicos (`REQ-001` a `REQ-010`), os contratos de dados, as decisões (`ADR-001` a `ADR-007`) e os testes (`TEST-001` a `TEST-013`). **A SPEC é a referência viva:** o código deve fazer exatamente o que ela diz.
4. Consulte `data/raw/garden_shop_dicionario_dados.xlsx` para o significado dos campos. Atenção: o dicionário diz que as datas estão em `DD/MM/AAAA`, mas os arquivos usam `AAAA-MM-DD` (SPEC ADR-004).
5. Este projeto não tem `CLAUDE.md`. Estas instruções valem para qualquer agente, inclusive o Claude Code.

### Resolução de conflitos

- Não ignore requisitos aprovados da SPEC sem registrar o conflito.
- Se o pedido do usuário contradisser o PRD ou a SPEC, **pare e pergunte** antes de implementar. Não "corrija" um documento em silêncio.
- Não invente regras de negócio. Exemplos do que **não** fazer: inventar prazo de entrega de fornecedor, usar `shipped_date` como prazo do fornecedor, "prever" ruptura sem histórico.
- A preservação dos dados (seção 5.3) prevalece sobre qualquer conveniência.

## 3. Processo de trabalho

### Etapa 1: Compreensão
- Leia a estrutura (seção 5.2) e o código relacionado à tarefa antes de propor mudanças.
- Verifique se a regra já existe em `garden_dashboard/metrics.py`.

### Etapa 2: Planejamento
- Identifique os `REQ`/`RN`/`CA` afetados.
- Divida em mudanças pequenas, **uma branch por mudança**: `docs/…`, `test/…`, `feat/…`, `fix/…`.
- Para uma regra de cálculo nova ou alterada, defina primeiro o resultado esperado, de preferência com um exemplo do recorte em `tests/fixtures/recorte/` calculado à mão.

### Etapa 3: Implementação
- **Testes antes do código:** faça um commit com o teste (falhando) e depois um commit com a implementação.
- Regras de cálculo **somente** em `metrics.py`, como funções puras. O `app.py` só chama funções e exibe resultados.
- Cada função de `metrics.py` cita na docstring o requisito que implementa (ex.: `RN-006`).

### Etapa 4: Verificação
- Rode `pytest` (todos os testes devem passar).
- Abra o app (`streamlit run app.py`) e confira a tela. Os testes de interface não pegam rótulos cortados nem cores erradas.
- Confira se algum número da tela mudou. Se mudou, ele precisa continuar batendo com o PRD §6.5.
- Informe explicitamente o que não foi possível executar.

### Etapa 5: Documentação e entrega
- Toda descoberta que mude o comportamento esperado atualiza **PRD e SPEC no mesmo PR** do código, com uma linha nova no histórico de versões de cada um.
- Se um cenário de aceitação mudar, atualize também `tests/test_base_completa.py` e, se for o caso, `tests/test_app.py`.
- Abra um PR com: o que mudou, quais `REQ`/`RN`/`CA` são afetados, os testes executados e um print, se a interface mudou.
- Integre com merge commit (sem squash), para preservar no histórico que os testes vieram antes do código.

## 4. Regras de desenvolvimento

### 4.1. Código
- Nomes de colunas internas em inglês (`units_sold`, `stock_value`). Textos da interface em português.
- Trate erros de dados com `DataError` (mensagem `"<arquivo>: <problema>"`). Não use `try/except` genérico que esconda a causa.
- Valide as entradas na fronteira (`loader.py`). Dentro de `metrics.py`, os dados já são confiáveis.
- Não adicione dependências sem necessidade. As atuais estão em `requirements.txt`.

### 4.2. Alterações no repositório
- Não altere configurações não relacionadas à tarefa.
- Não faça push nem merge sem a autorização do responsável (Lucas Girardi).
- Não descarte alterações do usuário.

### 4.3. Dependências e ambientes
- Use um ambiente virtual (`.venv`), sem instalar pacotes globalmente.
- Não atualize dependências em massa.

### 4.4. Segurança
- Não há segredos no projeto. Nunca adicione tokens ou senhas.
- `customers.csv` tem dados pessoais (nome, e-mail, telefone). **Não carregue nem exiba esse arquivo.**

## 5. Padrões específicos do projeto

### 5.1. Resumo

- **Linguagem principal:** Python 3.10+ (verificado com 3.13).
- **Gerenciador de dependências:** pip + `requirements.txt`.
- **Ambiente de desenvolvimento:** venv local.
- **Padrão de código:** PEP 8, linhas de até 120 caracteres, funções puras e docstrings com a referência ao requisito. Não há linter configurado.
- **Testes:** pytest (configurado em `pyproject.toml`) e `streamlit.testing.v1.AppTest` para a interface.
- **Validação estática:** não configurada.
- **Execução local:** `streamlit run app.py`.
- **Build:** não se aplica.
- **Documentação:** `PRD.md`, `SPEC.md` e `AGENTS.md` na raiz.

### 5.2. Estrutura de diretórios

```
app.py                         # Interface Streamlit: filtros, layout, mensagens. SEM fórmulas
garden_dashboard/
  loader.py                    # REQ-001: leitura e validação dos CSVs
  metrics.py                   # REQ-002 a REQ-008: todas as regras de negócio
  formatting.py                # REQ-010: moeda e números
tests/
  fixtures/recorte/            # Recorte VERBATIM dos CSVs (SPEC §13.1). Não edite à mão
  test_loader.py               # TEST-001 a TEST-003
  test_metrics.py              # TEST-004 a TEST-010
  test_base_completa.py        # TEST-011 (cenários CA do PRD)
  test_formatting.py           # TEST-012
  test_app.py                  # TEST-013 (interface)
data/raw/                      # Dados originais da Aula 1. SOMENTE LEITURA
.streamlit/config.toml         # Tema verde (sem vermelho), sem menu Deploy
requirements.txt · pyproject.toml
```

### 5.3. Cuidados com os dados

- **Nunca altere, renomeie, reformate ou sobrescreva arquivos em `data/raw/`** (RN-010). Para cenários de teste, use as fixtures de `tests/` ou DataFrames criados no próprio teste. Para simular arquivos ausentes, use uma pasta temporária e `GARDEN_DATA_DIR`.
- Pedidos `cancelled` **nunca** contam como venda. `pending` e `processing` contam como venda e como pedido em aberto (RN-001, RN-002).
- Produtos descontinuados **nunca** recebem recomendação de reposição (RN-004).
- **Não faça join direto de `products` com `order_items` para calcular estoque ou valor:** isso duplica o estoque. Agregue as vendas por produto primeiro (RN-008, ADR-003).
- O período filtra só as vendas. Estoque e valor são sempre a posição atual (RN-007).
- Não use vermelho (RN-011): use `st.warning`/`st.info`, nunca `st.error`, e nenhuma cor avermelhada nos gráficos.

## 6. Comandos de referência

| Finalidade | Comando | Status |
|---|---|---|
| Criar o ambiente virtual | `python -m venv .venv` | ⚠️ não verificado (no teste, as dependências foram instaladas direto no ambiente) |
| Ativar o ambiente (Linux/macOS) | `source .venv/bin/activate` | ⚠️ não verificado |
| Ativar o ambiente (Windows) | `.venv\Scripts\activate` | ⚠️ não verificado (sem máquina Windows no teste) |
| Instalação | `pip install -r requirements.txt` | ✅ verificado em 2026-11-01 (Linux, Python 3.13) |
| Execução local | `streamlit run app.py` → http://localhost:8501 | ✅ verificado em 2026-11-01 |
| Execução com outra pasta de dados | `GARDEN_DATA_DIR=/caminho streamlit run app.py` | ✅ verificado em 2026-11-01 (via TEST-013) |
| Testes (todos) | `pytest` → 66 testes | ✅ verificado em 2026-11-01 |
| Testes de um arquivo | `pytest tests/test_metrics.py -v` | ✅ verificado em 2026-11-01 |
| Conferir que os dados não mudaram | `git diff --stat data/raw` (saída vazia) | ✅ verificado em 2026-11-01 |
| Formatação / Lint / Tipos | não configurados no projeto | — |
| Build | não se aplica | — |

Não afirme que um comando foi executado se ele não foi. Quando verificar um comando ⚠️, troque o status para ✅ com a data no mesmo PR.

## 7. Critérios de qualidade (checklist de revisão)

Antes de aprovar qualquer alteração, **inclusive as feitas por IA**, confira:

- [ ] O comportamento bate com a SPEC? Se a SPEC mudou, o PRD continua coerente?
- [ ] Há teste para o caso novo, incluindo dados vazios e limites (ex.: estoque exatamente igual ao nível)?
- [ ] `pytest` passa?
- [ ] Os números da tela inicial continuam batendo com o CA-001 (5 · 1 · US$ 4.731,00 · 86 · 6)?
- [ ] `git diff --stat data/raw` está vazio?
- [ ] Nenhuma fórmula foi parar no `app.py`?
- [ ] Nada em vermelho?
- [ ] Os documentos foram atualizados e versionados?

Desconfie de sugestões da IA que: inventem colunas inexistentes, proponham previsões sem histórico, troquem o formato de data para o do dicionário, removam validações para "simplificar" ou calculem o estoque a partir de `order_items`.

## 8. Protocolo para dúvidas e bloqueios

Pergunte ao responsável quando:

- uma regra de negócio não estiver definida no PRD (ex.: novo status de pedido);
- houver conflito entre PRD, SPEC e dicionário de dados;
- a mudança alterar números dos cenários de aceitação;
- for preciso alterar algo em `data/raw/`.

Dúvidas pequenas e de baixo risco: adote a alternativa mais simples compatível com os padrões existentes e registre a decisão na SPEC.

## 9. Formato de entrega

Ao concluir uma tarefa, informe:

1. **Resumo:** o que foi implementado.
2. **Arquivos:** quais foram criados ou alterados.
3. **Decisões:** escolhas técnicas relevantes (e se viraram ADR).
4. **Testes:** comandos executados e resultados reais (ex.: `pytest` → 66 passed).
5. **Pendências:** limitações, riscos e o que não foi verificado.

## 10. Princípio geral

Priorize a correção dos números, a preservação dos dados e a aderência à SPEC, e não apenas produzir código rapidamente. Um indicador errado na reunião de reposição é pior do que um indicador a menos.

## 11. Histórico de alterações

| Versão | Data | Alteração |
|---|---|---|
| 1.0 | 2026-11-01 | Criação inicial, com os comandos ainda não verificados |
| 1.1 | 2026-11-01 | Comandos verificados após a implementação. Incluído `test_app.py` |
| 2.0 | 2026-11-01 | Reorganizado no modelo da Aula 2 (`templates/AGENTS.md`), com IDs alinhados ao PRD e à SPEC v2.0 |
