# SPEC: Dashboard de Estoque e Reposição da Garden Shop

| | |
|---|---|
| **Autor** | Lucas Girardi |
| **Versão** | 1.1 |
| **Implementa** | [PRD.md](PRD.md) v1.0 (os IDs `RF`, `RN` e `CA` se referem ao PRD) |
| **Status** | Referência viva: qualquer mudança de comportamento atualiza esta SPEC no mesmo PR |

---

## 1. Visão geral da arquitetura

```
data/raw/*.csv ──► loader.py ──► metrics.py ──► app.py (Streamlit)
  (somente leitura)  valida e tipa   regras e agregações   filtros e visualização
```

| Módulo | Responsabilidade | O que **não** faz |
|---|---|---|
| `garden_dashboard/loader.py` | Ler os 5 CSVs necessários, validar estrutura, tipos, chaves e domínios, e devolver DataFrames tipados | Não calcula regras de negócio. Não grava arquivos |
| `garden_dashboard/metrics.py` | Implementar RN-01 a RN-09: vendas efetivas, visão por produto, status, prioridade, filtros, indicadores e tabelas agregadas | Não lê arquivos. Não usa Streamlit |
| `garden_dashboard/formatting.py` | Formatar moeda e números no padrão brasileiro | Não calcula nada |
| `app.py` | Interface: filtros, cartões, gráficos, tabelas, mensagens de dados vazios e de erro | Não contém fórmulas. Tudo vem de `metrics.py` |
| `tests/` | Testes de `loader`, `metrics` e `formatting`, com o recorte manual e a base completa | — |

Toda regra de cálculo fica em funções puras de `metrics.py` (entrada: DataFrames e parâmetros; saída: DataFrame ou número). Assim ela pode ser testada sem a interface.

## 2. Entradas

### 2.1 Arquivos e campos usados

Somente as tabelas e os campos necessários são carregados. `customers.csv` **não** é lido (PRD §4).

| Arquivo | Chave primária | Campos usados | Campos ignorados |
|---|---|---|---|
| `products.csv` | `product_id` | `product_name`, `category_id` (FK), `supplier_id` (FK), `cost`, `quantity_on_hand`, `reorder_level`, `discontinued` | `price` |
| `categories.csv` | `category_id` | `category_name` | — |
| `suppliers.csv` | `supplier_id` | `supplier_name`, `contact_email` | `state` |
| `orders.csv` | `order_id` | `order_date`, `status` | `customer_id`, `shipped_date`, `coupon_code` |
| `order_items.csv` | `order_item_id` | `order_id` (FK), `product_id` (FK), `quantity` | `unit_price` |

### 2.2 Relacionamentos

```
categories 1 ── N products N ── 1 suppliers
                    │ 1
                    │ N
orders 1 ───── N order_items
```

A ligação `products` ↔ `order_items` é **1:N**. Um join direto repetiria `quantity_on_hand` e `cost` a cada item vendido. A prevenção dessa duplicação está na seção 5.

### 2.3 Parâmetros vindos da interface

| Parâmetro | Tipo | Padrão | Requisito |
|---|---|---|---|
| `start`, `end` | `date` | `default_period(orders)` = menor e maior `order_date` da base (15/01/2024 a 14/06/2024) | RF-07 |
| `categories` | lista de nomes | todas | RF-08 |
| `suppliers` | lista de nomes | todos | RF-09 |
| `include_discontinued` | `bool` | `False` | RF-10 |

## 3. Carga e validação (`loader.py`)

`load_data(data_dir: Path) -> dict[str, DataFrame]` lê os arquivos **apenas para leitura** (RN-10) e aplica as verificações abaixo. Qualquer falha gera `DataError` com mensagem no formato `"<arquivo>: <problema>"`. O app exibe essa mensagem e para, sem mostrar números parciais (RF-20).

| # | Verificação | Exemplo de mensagem |
|---|---|---|
| V1 | Arquivo existe | `products.csv: arquivo não encontrado em data/raw` |
| V2 | Colunas obrigatórias presentes | `products.csv: colunas ausentes: reorder_level` |
| V3 | Chave primária única e não nula | `orders.csv: order_id duplicado: 5` |
| V4 | Campos numéricos convertíveis e ≥ 0 (`cost`, `quantity_on_hand`, `reorder_level`, `quantity`) | `products.csv: valor inválido em cost (linha do product_id 3)` |
| V5 | `quantity` > 0 | `order_items.csv: quantity deve ser > 0` |
| V6 | `discontinued` ∈ {true, false}, sem diferenciar maiúsculas | `products.csv: discontinued inválido: 'sim'` |
| V7 | `status` ∈ {shipped, pending, processing, cancelled}, com espaços removidos e em minúsculas | `orders.csv: status desconhecido: 'returned'` |
| V8 | `order_date` no formato `AAAA-MM-DD` | `orders.csv: order_date inválida: '02/03/2024'` |
| V9 | Integridade referencial (FKs da seção 2.2) | `order_items.csv: product_id sem produto correspondente: 99` |

**Formato das datas:** o dicionário de dados diz `DD/MM/AAAA`, mas os arquivos usam `AAAA-MM-DD` (ISO). A carga segue o arquivo real e rejeita qualquer outro formato (V8), para não confundir dia e mês sem avisar.

**Valores ausentes**

| Campo | Ausência permitida? | Tratamento |
|---|---|---|
| `contact_email` | Sim | Exibido como `"não cadastrado"` (RF-14) |
| `shipped_date`, `coupon_code` | Sim | Não usados |
| Qualquer campo de 2.1 (exceto `contact_email`) | Não | `DataError` (V2/V4/V6/V7/V8) |

Saída: DataFrames com `discontinued: bool`, `order_date: datetime64`, numéricos como `float`/`int` e `status` normalizado.

## 4. Regras e fórmulas (`metrics.py`)

### 4.1 Vendas efetivas no período (RN-01, RN-02, RN-07)

```
sales_by_product(orders, order_items, start, end) -> DataFrame[product_id, units_sold]

pedidos_validos = orders WHERE status IN ('shipped','pending','processing')
                         AND start <= order_date <= end      -- datas inclusivas
units_sold(p)   = Σ order_items.quantity
                  WHERE order_id ∈ pedidos_validos AND product_id = p
```

O resultado tem **uma linha por produto** (agregação antes de qualquer join).

### 4.2 Pedidos em aberto (RF-05, RN-02)

```
open_orders_count(orders, order_items, start, end, product_ids) -> int
= nº de order_id DISTINTOS com status IN ('pending','processing'),
  start <= order_date <= end, e ao menos um item com product_id ∈ product_ids
```

`product_ids` são os produtos visíveis após os filtros. Assim, o indicador respeita categoria, fornecedor e descontinuados.

### 4.3 Visão por produto (RN-03 a RN-09)

`build_product_view(data, start, end) -> DataFrame` com **exatamente uma linha por produto** de `products.csv`:

| Coluna | Fórmula |
|---|---|
| `category_name`, `supplier_name`, `contact_email` | joins N:1 (não multiplicam linhas) |
| `units_sold` | `sales_by_product` com left join e ausência = 0 |
| `stock_value` | `quantity_on_hand × cost` |
| `pct_level` | `quantity_on_hand ÷ reorder_level`; `NaN` se `reorder_level = 0` |
| `deficit` | `max(reorder_level − quantity_on_hand, 0)`; 0 se descontinuado |
| `status` | tabela 4.4 |
| `needs_reorder` | `not discontinued AND reorder_level > 0 AND quantity_on_hand ≤ reorder_level` |
| `priority` | tabela 4.5 |

### 4.4 Status do estoque (RN-05). Avaliado na ordem, vale o primeiro que se aplica

| Ordem | Condição | Status |
|---|---|---|
| 1 | `discontinued` | Descontinuado |
| 2 | `reorder_level = 0` | Sem nível definido |
| 3 | `quantity_on_hand = 0` | Zerado |
| 4 | `pct_level ≤ 0,50` | Crítico |
| 5 | `pct_level ≤ 1,00` | Abaixo do nível |
| 6 | `pct_level ≤ 1,25` | Atenção |
| 7 | demais | OK |

### 4.5 Prioridade (RN-06)

`mediana` = mediana de `units_sold` de **todos os produtos ativos** no período, calculada em `build_product_view`, ou seja, antes dos filtros de categoria e fornecedor.

| Status | Condição adicional | Prioridade | Ordem de exibição |
|---|---|---|---|
| Zerado ou Crítico | — | P1 Urgente | 1 |
| Abaixo do nível | `units_sold ≥ mediana` | P2 Alta | 2 |
| Abaixo do nível | `units_sold < mediana` | P3 Média | 3 |
| Atenção | — | Monitorar | 4 |
| Descontinuado | — | Não repor | 5 |
| OK / Sem nível definido | — | — | 6 |

### 4.6 Filtros (RF-07 a RF-10)

`apply_filters(view, categories, suppliers, include_discontinued) -> DataFrame`

- Mantém linhas com `category_name ∈ categories` **e** `supplier_name ∈ suppliers`. Lista vazia = nenhum produto.
- Se `include_discontinued = False`, remove `discontinued = True`.
- O período **não** é aplicado aqui. Ele já entrou em `units_sold` (4.3) e só afeta vendas (RN-07).
- Se `start > end`, o app inverte as datas. Se o usuário escolher só uma data, `end = start`.

### 4.7 Indicadores (RF-01 a RF-05)

`compute_kpis(filtered_view, open_orders) -> dict`

| Chave | Fórmula sobre `filtered_view` |
|---|---|
| `products_to_reorder` | `Σ needs_reorder` |
| `zero_stock` | nº de linhas com `status = 'Zerado'` (descontinuados nunca têm esse status) |
| `stock_value` | `Σ stock_value` |
| `units_sold` | `Σ units_sold` |
| `open_orders` | valor de 4.2 |

Com `filtered_view` vazio, todos os valores são 0 (RF-17).

### 4.8 Tabelas para as visualizações

| Função | Saída | Requisito |
|---|---|---|
| `priority_table(view)` | linhas com prioridade P1, P2, P3, Monitorar ou Não repor, ordenadas por (ordem da prioridade, `pct_level`, `product_name`) | RF-11 |
| `sales_chart_data(view)` | todas as linhas do filtro (inclusive com 0 vendas), ordenadas por `units_sold` decrescente | RF-12 |
| `reorder_by_category(view)` | `category_name`, `products`, `to_reorder` | RF-13 |
| `supplier_summary(view)` | só produtos com `needs_reorder`: `supplier_name`, `products`, `deficit_total`, `contact_email` (ausente = "não cadastrado") | RF-14 |

## 5. Prevenção de duplicações (RN-08)

1. As vendas são agregadas por `product_id` (4.1) **antes** do join com `products`.
2. Os joins com `categories` e `suppliers` são N:1 e validados com `validate="many_to_one"` do pandas.
3. `build_product_view` verifica `len(view) == len(products)` e `product_id` único. Se falhar, gera um erro interno.
4. `stock_value` é calculado na tabela de produtos e nunca a partir de `order_items`.

Teste dedicado: ver T-08 na seção 8. Um join ingênuo `products ⨝ order_items` faria o Fiddle-Leaf Fig valer 4 × US$ 252 na base completa.

## 6. Saída: interface (`app.py`)

| Área | Conteúdo | Requisito |
|---|---|---|
| Barra lateral | Período, categoria, fornecedor, incluir descontinuados | RF-07 a RF-10 |
| Cabeçalho | Título, autor e nota com o período e "pedidos cancelados excluídos" | RF-16 |
| Linha de cartões | 5 indicadores, cada um com o rótulo "Posição atual" ou "Período" | RF-01 a RF-06 |
| Bloco principal | Lista de prioridades (largura total) | RF-11 |
| Bloco inferior | Gráfico de vendas por produto · gráfico de reposição por categoria · quadro de fornecedores | RF-12 a RF-14 |
| Expansível | Tabela de todos os produtos filtrados | RF-15 |

**Mensagens** (sempre `st.info`/`st.warning`, nunca `st.error`, por causa de RN-11)

| Situação | Mensagem |
|---|---|
| `filtered_view` vazio | "Nenhum produto encontrado para os filtros selecionados." |
| `units_sold` total = 0 | "Sem vendas efetivas no período selecionado." |
| Nenhum `needs_reorder` | "Nenhum produto precisa de reposição nos filtros selecionados." |
| `DataError` | "Não foi possível carregar os dados: <mensagem>" |

**Cores** (RN-11, sem vermelho): Zerado `#3B3B3B` · Crítico `#D9822B` · Abaixo do nível `#E8B931` · Atenção `#7A9CC6` · OK `#4F9A6B` · Descontinuado `#A8A8A8` · Sem nível definido `#B9A6D6`. O tema do Streamlit (`.streamlit/config.toml`) usa a cor primária `#1F4E3D`, porque o padrão do Streamlit é vermelho.

**Números:** `formatting.brl_usd(4731) → "US$ 4.731,00"` (valores em dólar, conforme o dicionário, com separadores brasileiros) e `formatting.brl_int(1234) → "1.234"`.

## 7. Exemplos com resultado esperado

### 7.1 Recorte manual (`tests/fixtures/recorte/`)

Linhas copiadas **sem alteração** dos CSVs originais: produtos 1, 9, 11, 14 e 24; pedidos 1, 7, 10, 17 e 18; apenas os itens desses pedidos que são desses produtos.

| Pedido | Data | Status | Itens (produto × qtd) |
|---|---|---|---|
| 1 | 2024-03-02 | shipped | Fiddle-Leaf Fig × 1 |
| 7 | 2024-05-01 | pending | Pruning Shears × 1, Hand Cultivator × 2 |
| 10 | 2024-02-28 | shipped | Fiddle-Leaf Fig × 1 |
| 17 | 2024-04-03 | **cancelled** | Pruning Shears × 1 |
| 18 | 2024-06-05 | shipped | Fiddle-Leaf Fig × 2 |

**Indicador validado 1: Unidades vendidas (período completo)**

| Produto | Cálculo | Unidades |
|---|---|---|
| Fiddle-Leaf Fig | 1 (ped. 1) + 1 (ped. 10) + 2 (ped. 18) | 4 |
| Pruning Shears | 1 (ped. 7, pending) + ~~1 (ped. 17, cancelado)~~ | 1 |
| Hand Cultivator | 2 (ped. 7, pending) | 2 |
| Hanging Basket | sem vendas | 0 |
| Bird Feeder | descontinuado, oculto por padrão | (0) |
| **Total** | | **7** |

**Indicador validado 2: Valor do estoque a custo**

| Produto | Estoque × custo | Valor |
|---|---|---|
| Fiddle-Leaf Fig | 14 × 18,00 | 252,00 |
| Pruning Shears | 18 × 11,00 | 198,00 |
| Hand Cultivator | 3 × 3,50 | 10,50 |
| Hanging Basket | 0 × 6,00 | 0,00 |
| **Total (padrão, sem descontinuados)** | | **US$ 460,50** |
| Bird Feeder (com descontinuados) | 4 × 8,00 | + 32,00 = **US$ 492,50** |

O Fiddle-Leaf Fig aparece em 3 pedidos, mas seu valor entra uma vez só (252,00, não 756,00).

**Demais resultados esperados no recorte**

| Verificação | Esperado | Por quê |
|---|---|---|
| Produtos a repor | 2 (Hand Cultivator, Hanging Basket) | 3 ≤ 10 e 0 ≤ 10. O Bird Feeder (4 ≤ 6) é descontinuado |
| Produtos zerados | 1 (Hanging Basket) | |
| Pedidos em aberto | 1 (pedido 7) | O pedido 17 é cancelado, não fica em aberto |
| Status | Fiddle OK (140%) · Shears OK (225%) · Cultivator Crítico (30%) · Basket Zerado · Bird Feeder Descontinuado | Tabela 4.4 |
| Prioridade | Cultivator e Basket = P1 Urgente · Bird Feeder = Não repor (com descontinuados) | Tabela 4.5 |
| Mediana de vendas (ativos) | 1,5 (vendas 4, 1, 2, 0) | |
| Período 01/03/2024 a 31/05/2024 | Unidades = 4 (Fiddle 1, Shears 1, Cultivator 2); Pedidos em aberto = 1; Valor = 460,50 (inalterado) | Só os pedidos 1 e 7 são válidos no período (RN-07) |
| Fornecedores a contatar | Ironwood Tools (1 produto, déficit 7, "não cadastrado") · Terra Pots Co (1, déficit 10, hello@terrapots.example) | |

### 7.2 Base completa (`data/raw/`)

São os mesmos números dos critérios CA-01 a CA-10 do PRD, verificados por `tests/test_base_completa.py`.

| Verificação | Esperado |
|---|---|
| Padrão | a repor 5 · zerados 1 · valor US$ 4.731,00 · unidades 86 · em aberto 6 |
| Mediana (ativos, período completo) | 3 → Pothos (5) = P2, Orchid Food (2) = P3 |
| Com descontinuados | valor US$ 4.763,00 · a repor 5 |
| Categoria Tools | a repor 1 · valor US$ 448,50 · unidades 5 |
| Fornecedor RootWorks Supply | 0 produtos · indicadores 0 |
| Julho/2024 | unidades 0 · em aberto 0 · a repor 5 · valor 4.731,00 |

## 8. Plano de testes (escritos antes da implementação)

| ID | Arquivo | O que verifica | Requisitos |
|---|---|---|---|
| T-01 | `test_loader.py` | Carga do recorte: tipos, `discontinued` booleano, status normalizado | — |
| T-02 | `test_loader.py` | `DataError` para arquivo ausente, coluna ausente, PK duplicada, status desconhecido, data fora do formato, FK inválida e número negativo | RF-20, V1 a V9 |
| T-03 | `test_loader.py` | Os arquivos de origem não são alterados (hash antes e depois) | RN-10 |
| T-04 | `test_metrics.py` | Unidades vendidas por produto = 7 no recorte; cancelado excluído | RN-01, RN-02 |
| T-05 | `test_metrics.py` | Valor do estoque = 460,50 / 492,50 | RF-03, RN-04 |
| T-06 | `test_metrics.py` | Status e prioridade de cada faixa, inclusive limites exatos (50%, 100%, 125%) e `reorder_level = 0` | RN-03, RN-05, RN-06 |
| T-07 | `test_metrics.py` | Descontinuado nunca `needs_reorder`, nunca conta em RF-01/RF-02, prioridade "Não repor" | RN-04 |
| T-08 | `test_metrics.py` | Uma linha por produto; o valor do produto com vários pedidos não duplica | RN-08 |
| T-09 | `test_metrics.py` | Filtros sem resultado → indicadores 0 e tabelas vazias sem exceção; período sem vendas → unidades 0 e estoque inalterado | RF-17 a RF-19, RN-07 |
| T-10 | `test_metrics.py` | Pedidos em aberto respeitam período e produtos visíveis | RF-05 |
| T-11 | `test_base_completa.py` | Período padrão e critérios CA-01 a CA-10 na base real | RF-07, CA-01 a CA-10 |
| T-12 | `test_formatting.py` | `US$ 4.731,00`, `US$ 0,00`, `US$ 448,50`, `1.234` | — |

## 9. Histórico de versões

| Versão | Mudança |
|---|---|
| 1.0 | Primeira versão, escrita antes do código, a partir do PRD v1.0 |
| 1.1 | Incluídas `default_period` (§2.3) e `brl_int` (§6), que surgiram ao escrever os testes T-11 e T-12. O período padrão deixa de ser calculado na interface e passa a ser uma função testável |
