# AGENTS.md: instruções para agentes de IA neste repositório

Projeto de **Lucas Girardi**: dashboard de estoque e reposição da Garden Shop (Python + Streamlit).
Este arquivo orienta qualquer agente de IA (ou pessoa) que vá alterar o repositório. Leia-o inteiro antes de começar.

## 1. Documentos a consultar, nesta ordem

1. **[PRD.md](PRD.md)**: *o quê* e *por quê*. Requisitos `RF-xx`, regras `RN-xx` e critérios de aceitação `CA-xx`.
2. **[SPEC.md](SPEC.md)**: *como*. Fórmulas, filtros, validações, módulos e exemplos com resultado esperado. **É a referência viva:** o código deve fazer exatamente o que a SPEC diz.
3. `data/raw/garden_shop_dicionario_dados.xlsx`: significado e valores válidos de cada campo. Atenção à divergência do formato de data descrita na SPEC §3.

Se o pedido do usuário contradisser o PRD ou a SPEC, **pare e pergunte** antes de implementar. Não "corrija" o documento em silêncio.

## 2. Preparação do ambiente

Requisito: Python 3.10 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Comandos

| Ação | Comando | Verificado? |
|---|---|---|
| Rodar todos os testes | `pytest` | ⚠️ ainda não verificado |
| Rodar um arquivo de teste | `pytest tests/test_metrics.py -v` | ⚠️ ainda não verificado |
| Abrir o dashboard | `streamlit run app.py` (abre em http://localhost:8501) | ⚠️ ainda não verificado |
| Criar o ambiente virtual no Windows | `.venv\Scripts\activate` | ⚠️ ainda não verificado |

> Quando um comando for executado com sucesso, troque "⚠️ ainda não verificado" por "✅ verificado em <data>" no mesmo PR.

## 4. Organização do código

```
app.py                         # Interface Streamlit: só filtros, layout e mensagens. Sem fórmulas
garden_dashboard/
  loader.py                    # Leitura e validação dos CSVs (SPEC §3)
  metrics.py                   # Todas as regras de negócio (SPEC §4 e §5), em funções puras
  formatting.py                # Formatação de moeda e números
tests/
  fixtures/recorte/            # Pequeno recorte VERBATIM dos CSVs, base dos exemplos da SPEC §7.1
  test_loader.py               # T-01 a T-03
  test_metrics.py              # T-04 a T-10
  test_base_completa.py        # T-11 (critérios de aceitação do PRD)
  test_formatting.py           # T-12
data/raw/                      # Dados originais da Aula 1. SOMENTE LEITURA
.streamlit/config.toml         # Tema (cor primária verde, sem vermelho)
```

Regras de organização:
- Fórmulas e regras de negócio ficam **somente** em `metrics.py`. O `app.py` apenas chama funções e exibe resultados.
- Cada função de `metrics.py` deve citar na docstring o requisito que implementa (ex.: `RN-06`).
- Nomes de colunas internas em inglês (`units_sold`, `stock_value`). Textos da interface em português.

## 5. Cuidados com os dados

- **Nunca altere, renomeie, reformate ou sobrescreva arquivos em `data/raw/`** (RN-10). Para cenários de teste, crie fixtures em `tests/` ou DataFrames dentro do próprio teste.
- `customers.csv` fica no repositório para preservar a base original, mas **não é carregado** (PRD §4).
- Pedidos `cancelled` **nunca** contam como venda (RN-01). `pending` e `processing` contam como venda e como pedido em aberto (RN-02).
- Produtos descontinuados **nunca** recebem recomendação de reposição (RN-04).
- **Não faça join direto de `products` com `order_items` para calcular estoque ou valor:** isso duplica o estoque. Agregue as vendas por produto primeiro (SPEC §5).
- O período filtra só as vendas. Estoque e valor são sempre a posição atual (RN-07).
- Datas estão em `AAAA-MM-DD` nos arquivos, mesmo que o dicionário diga `DD/MM/AAAA`.
- Não use vermelho em nenhum elemento visual (RN-11). Use `st.warning`/`st.info`, nunca `st.error`.

## 6. Fluxo de trabalho

1. Crie uma branch por mudança pequena: `docs/...`, `test/...`, `feat/...`, `fix/...`.
2. **Para regras de cálculo, escreva o teste antes da implementação**, com o resultado esperado da SPEC §7. Faça um commit do teste (falhando) e depois um commit da implementação.
3. Rode `pytest` e abra o app para conferir visualmente antes de abrir o PR.
4. Abra um PR com: o que mudou, quais `RF`/`RN`/`CA` são afetados, como foi testado e um print, se a interface mudou.
5. Integre com merge (sem squash), para preservar o histórico de testes antes do código.

## 7. Revisão das alterações

Antes de aprovar qualquer alteração, inclusive as feitas por IA, confira:

- [ ] O comportamento bate com a SPEC? Se a SPEC mudou, o PRD continua coerente?
- [ ] Os testes cobrem o caso novo, incluindo dados vazios e limites (ex.: estoque exatamente igual ao nível)?
- [ ] `pytest` passa?
- [ ] Algum número da tela mudou? Se mudou, ele ainda bate com os critérios CA do PRD?
- [ ] Nenhum arquivo em `data/raw/` foi modificado? (`git diff --stat data/raw` deve vir vazio)
- [ ] Nenhuma fórmula foi parar no `app.py`?
- [ ] Nada em vermelho?

Desconfie de sugestões da IA que: inventem colunas inexistentes (ex.: prazo de entrega), proponham previsões sem histórico, usem `shipped_date` como prazo do fornecedor, ou "simplifiquem" excluindo a validação de dados.

## 8. Atualização dos documentos

- Toda descoberta que mude o comportamento esperado atualiza **PRD e SPEC no mesmo PR** do código, com uma linha nova no histórico de versões de cada um.
- Se um critério de aceitação mudar, atualize também `tests/test_base_completa.py`.
- Comandos novos entram na tabela da seção 3, marcados como não verificados até serem executados.
