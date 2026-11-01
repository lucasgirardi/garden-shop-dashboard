# PRD: Dashboard de Estoque e Reposição da Garden Shop

| | |
|---|---|
| **Autor** | Lucas Girardi |
| **Versão** | 1.1 (alinhada ao dashboard implementado) |
| **Documentos relacionados** | [SPEC.md](SPEC.md) (como cada requisito é implementado) · [AGENTS.md](AGENTS.md) (como trabalhar no repositório) |
| **Origem** | Proposta da Aula 1 (Lista 01), com escopo revisado nesta entrega (ver seção 9) |

Os requisitos têm identificadores (`RF`, `RN`, `CA`) para serem referenciados na SPEC, nos testes e nos PRs.

---

## 1. Problema

A Garden Shop é uma loja virtual de jardinagem com 24 produtos em 8 categorias, fornecidos por 6 fornecedores. Hoje a equipe de gestão tem dificuldade para:

1. identificar rapidamente quais produtos precisam de reposição;
2. avaliar se o estoque é suficiente diante das vendas;
3. priorizar os itens e saber com qual fornecedor falar.

Os dados existem (produtos, pedidos, itens, fornecedores), mas estão em arquivos separados. Cruzá-los manualmente é lento e sujeito a erros, como contar pedidos cancelados como venda ou recomendar a compra de um produto descontinuado.

## 2. Usuários

| Usuário | O que precisa | Como usa o dashboard |
|---|---|---|
| **Gestão da loja** (usuário principal) | Visão geral do estoque e da prioridade de reposição | Lê os indicadores e a lista de prioridades na reunião semanal de reposição |
| **Comprador / operação** | Saber o que comprar, quanto e de quem | Filtra por fornecedor e usa o déficit e o contato do fornecedor para fazer o pedido |

## 3. Objetivos

| ID | Objetivo | Como saberemos que foi atingido |
|---|---|---|
| OBJ-1 | Mostrar em segundos quais produtos precisam de reposição | Indicador "Produtos a repor" e lista de prioridades visíveis sem rolar a página |
| OBJ-2 | Relacionar o estoque com as vendas efetivas | Gráfico de vendas do período colorido pelo status do estoque |
| OBJ-3 | Apoiar a priorização e o contato com fornecedores | Lista ordenada por prioridade, com fornecedor, e quadro de fornecedores com contato |
| OBJ-4 | Mostrar o capital imobilizado em estoque | Indicador de valor do estoque a custo |

## 4. Escopo

**Dentro do escopo**
- Dashboard web local (Streamlit) que lê os CSVs originais da Aula 1 sem alterá-los.
- 5 indicadores, 4 filtros, 2 gráficos, 2 tabelas de apoio à decisão e 1 tabela de detalhe (seção 5).
- Regras de vendas efetivas, reposição, descontinuados e prioridade (seção 6).
- Testes automatizados das regras de cálculo.

**Fora do escopo (exclusões)**

| Exclusão | Motivo |
|---|---|
| Previsão de demanda, data de ruptura, ponto de pedido, estoque de segurança | Não há histórico de movimentação de estoque nem prazo de entrega dos fornecedores |
| Giro de estoque e cobertura em meses | Exigem estoque médio ou histórico. Com 23 pedidos válidos em cerca de 5 meses, a cobertura seria só indicativa e poderia induzir a erro (estava na proposta da Aula 1 e foi removida) |
| Quantidade ideal de compra | Não existe nível máximo, lote mínimo nem custo de pedido. O dashboard mostra apenas o déficit mínimo |
| Simular o estoque descontando pedidos em aberto | O enunciado define `quantity_on_hand` como o estoque atual. A opção prevista na Aula 1 foi removida (seção 9) |
| Análise de clientes (`customers.csv`) | Não contribui para a decisão de reposição |
| Edição de dados, login, hospedagem na internet | Não necessários para o uso local proposto |

## 5. Requisitos funcionais

### 5.1 Indicadores (cartões no topo)

| ID | Indicador | Referência temporal | Por que é útil |
|---|---|---|---|
| RF-01 | **Produtos a repor**: quantidade de produtos ativos com estoque ≤ nível de reposição | Posição atual | Dimensiona o problema e responde "quantos itens preciso comprar?" |
| RF-02 | **Produtos zerados**: quantidade de produtos ativos com estoque = 0 | Posição atual | Estoque zero significa venda perdida, o caso mais urgente |
| RF-03 | **Valor do estoque a custo**: Σ estoque × custo | Posição atual | Mostra o capital imobilizado (pergunta da gestão na Aula 1) |
| RF-04 | **Unidades vendidas**: Σ unidades em vendas efetivas | Período selecionado | Mostra o ritmo de vendas no recorte analisado |
| RF-05 | **Pedidos em aberto**: pedidos `pending` + `processing` | Período selecionado | Mostra a demanda já vendida que ainda não saiu da loja |

> **RF-06.** Cada cartão deve informar se se refere à **posição atual do estoque** ou ao **período de vendas**. Os filtros de período não alteram os indicadores de estoque (RN-07).

### 5.2 Filtros (barra lateral)

| ID | Filtro | Padrão | Por que é útil |
|---|---|---|---|
| RF-07 | **Período de vendas** (data inicial e final) | Primeira e última data de pedido da base | Permite analisar as vendas de um intervalo específico |
| RF-08 | **Categoria** (seleção múltipla) | Todas | Focar uma linha de produtos |
| RF-09 | **Fornecedor** (seleção múltipla) | Todos | Preparar a conversa com um fornecedor |
| RF-10 | **Incluir descontinuados** (liga/desliga) | Desligado | Consultar descontinuados sem misturá-los com a reposição |

### 5.3 Visualizações e tabelas

| ID | Elemento | Por que é útil |
|---|---|---|
| RF-11 | **Lista de prioridades de reposição** (tabela): produto, categoria, fornecedor, estoque, nível, déficit, unidades vendidas no período, status e prioridade, ordenada da maior para a menor prioridade | É o elemento central: responde "o que comprar primeiro e de quem" |
| RF-12 | **Unidades vendidas por produto** (barras horizontais, cor = status do estoque) | Cruza vendas e estoque no mesmo visual. Produtos sem vendas aparecem com zero |
| RF-13 | **Produtos a repor por categoria** (barras) | Mostra onde se concentram os problemas |
| RF-14 | **Fornecedores dos produtos a repor** (tabela): fornecedor, nº de produtos, déficit total, e-mail | Indica com quem falar. E-mail ausente aparece como "não cadastrado" |
| RF-15 | **Tabela de todos os produtos filtrados** (seção expansível), com estoque, custo, valor e vendas | Permite conferir os números dos indicadores |
| RF-16 | **Legenda e notas**: período usado, exclusão de cancelados e o fato de os descontinuados estarem ocultos ou visíveis | Evita interpretações erradas |

### 5.4 Situações sem dados e erros

| ID | Situação | Comportamento esperado |
|---|---|---|
| RF-17 | Filtros sem nenhum produto (ex.: fornecedor sem produtos) | Indicadores mostram 0 / US$ 0,00. No lugar das visualizações aparece o aviso "Nenhum produto encontrado para os filtros selecionados". O app não quebra |
| RF-18 | Período sem pedidos | Unidades vendidas = 0 e pedidos em aberto = 0. Os indicadores de estoque continuam iguais. O gráfico de vendas mostra o aviso "Sem vendas efetivas no período selecionado" |
| RF-19 | Nenhum produto a repor nos filtros | A lista de prioridades e o quadro de fornecedores mostram "Nenhum produto precisa de reposição nos filtros selecionados" |
| RF-20 | Arquivo ausente, coluna faltando ou dado inválido | O app mostra uma mensagem clara, com o arquivo e o problema, e não exibe números parciais |

## 6. Regras de negócio

| ID | Regra |
|---|---|
| RN-01 | **Venda efetiva** = itens de pedidos com status `shipped`, `pending` ou `processing`. Pedidos `cancelled` nunca entram em vendas. |
| RN-02 | **Tratamento dos status:** `shipped` = venda concluída e enviada. `pending` e `processing` = venda efetiva ainda não enviada: entram nas vendas (o cliente comprou) e também no indicador de pedidos em aberto. |
| RN-03 | **Necessidade de reposição:** produto ativo com `reorder_level > 0` e `quantity_on_hand ≤ reorder_level`. Usa "≤" porque, ao atingir o nível de referência, a reposição já deve ser disparada. |
| RN-04 | **Descontinuados** (`discontinued = true`) nunca são recomendados para reposição e nunca entram em RF-01 e RF-02. Ficam ocultos por padrão. Quando exibidos (RF-10), aparecem com o status "Descontinuado" e a prioridade "Não repor". |
| RN-05 | **Status do estoque** (produtos ativos, `pct = estoque ÷ nível`): Zerado (estoque = 0) · Crítico (pct ≤ 50%) · Abaixo do nível (50% < pct ≤ 100%) · Atenção (100% < pct ≤ 125%) · OK (pct > 125%) · Sem nível definido (`reorder_level = 0`). |
| RN-06 | **Prioridade:** P1 Urgente = Zerado ou Crítico · P2 Alta = Abaixo do nível e vendas no período ≥ mediana · P3 Média = Abaixo do nível e vendas < mediana · Monitorar = Atenção · "—" = demais. A mediana é calculada sobre as vendas no período de todos os produtos ativos, sem os filtros de categoria e fornecedor, para que a prioridade de um item não mude conforme o recorte. |
| RN-07 | **Período × posição atual:** o período filtra apenas pedidos (RF-04, RF-05, RF-12 e a coluna de vendas). Estoque, valor, status e déficit vêm sempre da posição atual (`quantity_on_hand`). |
| RN-08 | **Sem duplicação:** o estoque e o valor são calculados uma única vez por produto. As vendas são agregadas por produto antes de serem ligadas à tabela de produtos. |
| RN-09 | **Déficit** = `max(reorder_level − quantity_on_hand, 0)`. É o mínimo para voltar ao nível de referência, não uma sugestão de lote de compra. |
| RN-10 | **Dados originais preservados:** os CSVs em `data/raw/` são somente leitura. Nenhuma etapa grava sobre eles. |
| RN-11 | **Cores:** o dashboard não usa vermelho (cor reservada às correções do professor). |

## 7. Critérios de aceitação (observáveis com a base da Aula 1)

Todos os critérios consideram os filtros padrão, salvo indicação contrária.

| ID | Cenário | Resultado esperado | Requisitos |
|---|---|---|---|
| CA-01 | Abrir o dashboard | Produtos a repor = **5**; Produtos zerados = **1**; Valor do estoque = **US$ 4.731,00**; Unidades vendidas = **86**; Pedidos em aberto = **6** | RF-01 a RF-05 |
| CA-02 | Lista de prioridades | P1: Hanging Basket, Tomato Seeds 'Roma', Hand Cultivator · P2: Pothos 'Golden' · P3: Orchid Food · Monitorar: Solar Lantern | RF-11, RN-05, RN-06 |
| CA-03 | Pedido cancelado (pedido 17, 1 Pruning Shears) | Pruning Shears mostra **1** unidade vendida (e não 2) | RN-01 |
| CA-04 | Ligar "Incluir descontinuados" | Bird Feeder aparece com status "Descontinuado" e prioridade "Não repor". Produtos a repor continua **5**. Valor do estoque passa a **US$ 4.763,00** | RF-10, RN-04 |
| CA-05 | Filtrar categoria = Tools | Produtos a repor = **1** (Hand Cultivator); Valor = **US$ 448,50**; Unidades vendidas = **5** | RF-08 |
| CA-06 | Filtrar fornecedor = RootWorks Supply (sem produtos) | Indicadores zerados e aviso "Nenhum produto encontrado…", sem erro | RF-17 |
| CA-07 | Período 01/07/2024 a 31/07/2024 | Unidades vendidas = **0**; Pedidos em aberto = **0**; Produtos a repor = **5** e valor = **US$ 4.731,00** (inalterados) | RF-18, RN-07 |
| CA-08 | Produto sem vendas (Hanging Basket) | Aparece no gráfico e na lista com **0** unidades vendidas | RF-12 |
| CA-09 | Produto em vários pedidos (Fiddle-Leaf Fig, 4 pedidos) | Valor do estoque do produto = **US$ 252,00** (14 × 18), contado uma vez só | RN-08 |
| CA-10 | Ironwood Tools no quadro de fornecedores | E-mail aparece como "não cadastrado" | RF-14 |
| CA-11 | Arquivo `products.csv` ausente ou com coluna faltando | Mensagem clara com o nome do arquivo e sem números parciais | RF-20 |
| CA-12 | Rodar `pytest` | Todos os testes passam. CA-01 a CA-10 são verificados na base real (`test_base_completa.py`) e CA-01, CA-04 a CA-07 e CA-11 também pela interface (`test_app.py`) | RN-01 a RN-11 |

## 8. Premissas e limitações

- `quantity_on_hand` é a posição atual do estoque, sem data de referência. As vendas vão de 15/01/2024 a 14/06/2024. Por isso o dashboard mostra lado a lado uma foto atual do estoque e um período de vendas.
- Sem histórico de movimentação, não é possível saber se um produto sem vendas não vende ou se não vendeu **por estar em falta** (caso do Hanging Basket).
- Sem prazo de entrega, a prioridade não considera a demora de cada fornecedor.
- O dicionário de dados indica datas em `DD/MM/AAAA`, mas os CSVs usam `AAAA-MM-DD`. A implementação segue o formato real dos arquivos (ver SPEC §3).
- O volume de vendas é pequeno (23 pedidos válidos). Rankings e a mediana de RN-06 são sensíveis a um único pedido.

## 9. Revisões de escopo e histórico de versões

**Revisões em relação à proposta da Aula 1**

| Mudança | Motivo |
|---|---|
| Removida a cobertura de estoque em meses | Pouco confiável com 23 pedidos em cerca de 5 meses. Poderia induzir a erro |
| Removido o filtro "Descontar pedidos em aberto" | O enunciado da Aula 2 define `quantity_on_hand` como o estoque atual |
| Removido o filtro de status do estoque | A lista de prioridades já ordena por gravidade. Menos controles deixam a tela mais simples |
| Incluído o status "Sem nível definido" (`reorder_level = 0`) | Evita divisão por zero e evita recomendar a reposição de um item sem política de estoque |
| A mediana da prioridade (RN-06) passa a ignorar os filtros de categoria e fornecedor | Sem isso, a prioridade de um produto mudaria conforme o recorte escolhido |

**Histórico de versões**

| Versão | Mudança |
|---|---|
| 1.0 | Primeira versão validada antes da implementação |
| 1.1 | Revisão final: contagem de elementos visuais corrigida (2 gráficos e 2 tabelas, e não "3 visualizações") e CA-12 passa a indicar onde cada critério é testado. Nenhuma regra mudou |
