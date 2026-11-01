# PRD: Product Requirements Document

> **Objetivo:** definir o problema, os usuários, os objetivos e os requisitos do dashboard de estoque e reposição da Garden Shop antes da implementação.

## 1. Identificação do projeto

- **Nome do projeto:** Garden Shop: Dashboard de Estoque e Reposição
- **Versão do documento:** 2.0
- **Status:** Aprovado (implementado e verificado)
- **Responsável:** Lucas Girardi
- **Data:** 2026-11-01

## 2. Visão geral

### 2.1. Contexto

A Garden Shop é uma loja virtual de jardinagem com 24 produtos em 8 categorias, fornecidos por 6 fornecedores. A base disponível (Aula 1) tem seis arquivos CSV (produtos, categorias, fornecedores, clientes, pedidos e itens de pedido) e um dicionário de dados. Na Aula 1 foi feita uma proposta de dashboard. Este documento revisa essa proposta para uma versão funcional.

### 2.2. Problema

A equipe de gestão não consegue identificar rapidamente quais produtos precisam de reposição, avaliar se o estoque é suficiente diante das vendas, nem priorizar os itens e saber com qual fornecedor falar. Os dados estão em arquivos separados. Cruzá-los manualmente é lento e sujeito a erros, como contar pedidos cancelados como venda, recomendar a compra de um produto descontinuado ou somar o estoque várias vezes ao ligar produtos a itens de pedido. A consequência é ruptura de estoque (venda perdida) e compras mal priorizadas.

### 2.3. Solução proposta

Um dashboard web local que lê os CSVs originais (sem alterá-los), aplica as regras de negócio deste PRD e mostra: indicadores de estoque e de vendas, uma lista de prioridades de reposição, gráficos de vendas e de reposição por categoria e um quadro de fornecedores, com filtros por período, categoria, fornecedor e descontinuados.

### 2.4. Proposta de valor

Em uma única tela, a gestão sabe **o que repor, com que urgência e de quem comprar**, com números confiáveis: sem cancelados, sem descontinuados e sem duplicação de estoque.

## 3. Objetivos e resultados esperados

### 3.1. Objetivos

- **OBJ-1:** mostrar em segundos quais produtos precisam de reposição.
- **OBJ-2:** relacionar o estoque atual com as vendas efetivas de um período.
- **OBJ-3:** apoiar a priorização das compras e o contato com fornecedores.
- **OBJ-4:** mostrar o capital imobilizado em estoque.

### 3.2. Indicadores de sucesso

| Indicador | Situação atual | Meta | Como medir |
|---|---|---|---|
| Tempo para identificar os produtos a repor | Cruzamento manual de 3 a 4 arquivos | Visível ao abrir o dashboard, sem rolar a página | Abrir o app (CA-001) |
| Correção dos indicadores | Sem conferência | 100% dos cenários CA-001 a CA-011 atendidos | `pytest` (TEST-011 e TEST-013) |
| Itens indevidos na lista de reposição | Risco de incluir descontinuados e cancelados | Zero | TEST-004 e TEST-007 |

### 3.3. Critérios de sucesso

- Os indicadores da tela inicial batem com os cálculos manuais (CA-001).
- Nenhum descontinuado aparece como "a repor" e nenhum cancelado conta como venda.
- Filtros sem resultado e períodos sem vendas não quebram o app.

## 4. Usuários e necessidades

### 4.1. Público-alvo

| Usuário | Contexto de uso |
|---|---|
| **Gestão da loja** (principal) | Reunião semanal de reposição: lê os indicadores e a lista de prioridades |
| **Comprador / operação** | Prepara pedidos de compra: filtra por fornecedor e usa o déficit e o contato |

### 4.2. Necessidades dos usuários

- Como **gestor**, quero ver quantos produtos precisam de reposição e quais estão zerados, para dimensionar o problema.
- Como **gestor**, quero uma lista ordenada por urgência, para decidir o que comprar primeiro.
- Como **gestor**, quero comparar o estoque com as vendas de um período, para avaliar se o estoque é suficiente.
- Como **comprador**, quero ver os fornecedores dos itens a repor, o déficit e o e-mail, para fazer os pedidos.
- Como **gestor**, quero saber o valor do estoque a custo, para acompanhar o capital imobilizado.

### 4.3. Jornada principal

1. O usuário executa `streamlit run app.py` e abre o dashboard no navegador.
2. Lê os 5 indicadores e a lista de prioridades com os filtros padrão (todo o período de vendas, todas as categorias e fornecedores, sem descontinuados).
3. Ajusta os filtros (por exemplo, um fornecedor) e consulta os gráficos e o quadro de fornecedores.
4. Usa a lista e o quadro de fornecedores para definir as compras da semana.

## 5. Escopo do produto

### 5.1. Incluído no escopo

- Leitura e validação dos 5 CSVs necessários, sem alterar os originais.
- 5 indicadores, 4 filtros, 2 gráficos, 2 tabelas de apoio à decisão e 1 tabela de detalhe (seção 6).
- Regras de vendas efetivas, reposição, descontinuados, prioridade e prevenção de duplicação (seção 9).
- Mensagens para filtros sem resultado, período sem vendas e dados inválidos.
- Testes automatizados das regras e da interface.

### 5.2. Fora do escopo

| Fora do escopo | Motivo |
|---|---|
| Previsão de demanda, data de ruptura, ponto de pedido, estoque de segurança | Não há histórico de movimentação nem prazo de entrega dos fornecedores |
| Giro de estoque e cobertura em meses | Exigem estoque médio ou histórico. Com 23 pedidos válidos em cerca de 5 meses, a cobertura seria só indicativa (estava na proposta da Aula 1 e foi removida) |
| Quantidade ideal de compra | Não existe nível máximo, lote mínimo nem custo de pedido. O dashboard mostra o déficit mínimo |
| Simular o estoque descontando pedidos em aberto | O enunciado define `quantity_on_hand` como o estoque atual (estava na Aula 1 e foi removido) |
| Análise de clientes (`customers.csv`) | Não contribui para a decisão de reposição |
| Edição de dados, login, hospedagem na internet | Desnecessários para o uso local |

### 5.3. Premissas

- `quantity_on_hand` é a posição atual do estoque, sem data de referência.
- Os pedidos vão de 15/01/2024 a 14/06/2024. O estoque é uma foto atual, não uma posição nessas datas.
- `reorder_level` é a referência oficial de reposição definida pela loja.
- Valores monetários estão em dólares (US$), conforme o dicionário.

### 5.4. Restrições

- **Orçamento:** nenhum (ferramentas gratuitas).
- **Prazo:** entrega da Lista 02.
- **Infraestrutura:** execução local. Não é obrigatório hospedar.
- **Tecnologia:** Python 3.10+, Streamlit, pandas, Altair, pytest.
- **Operação:** os arquivos em `data/raw/` não podem ser alterados. Nada em vermelho (cor reservada às correções).

## 6. Requisitos funcionais

### 6.1. Indicadores

| ID | Requisito | Prioridade | Critério de aceitação |
|---|---|---|---|
| RF-001 | O sistema deve mostrar **Produtos a repor**: produtos ativos com estoque ≤ nível de reposição (posição atual) | Must | Com os filtros padrão, mostra **5** |
| RF-002 | O sistema deve mostrar **Produtos zerados**: produtos ativos com estoque = 0 (posição atual) | Must | Com os filtros padrão, mostra **1** |
| RF-003 | O sistema deve mostrar o **Valor do estoque a custo** = Σ estoque × custo (posição atual) | Must | Com os filtros padrão, mostra **US$ 4.731,00** |
| RF-004 | O sistema deve mostrar as **Unidades vendidas** em vendas efetivas no período | Must | Com os filtros padrão, mostra **86** |
| RF-005 | O sistema deve mostrar os **Pedidos em aberto** (`pending` + `processing`) no período | Should | Com os filtros padrão, mostra **6** |
| RF-006 | Cada indicador deve informar se se refere à "Posição atual" ou ao "Período selecionado" | Must | Rótulo visível abaixo de cada cartão |

### 6.2. Filtros

| ID | Requisito | Prioridade | Critério de aceitação |
|---|---|---|---|
| RF-007 | Filtro de **período de vendas**, cujo padrão é da primeira à última data de pedido | Must | O padrão é 15/01/2024 a 14/06/2024. Alterar o período muda só as vendas (RN-007) |
| RF-008 | Filtro de **categoria** (seleção múltipla, padrão: todas) | Must | Categoria = Tools → a repor 1, valor US$ 448,50, unidades 5 |
| RF-009 | Filtro de **fornecedor** (seleção múltipla, padrão: todos) | Must | Fornecedor sem produtos → indicadores zerados e aviso |
| RF-010 | Opção **Incluir descontinuados** (padrão: desligada) | Should | Ligada → Bird Feeder visível como "Não repor", valor US$ 4.763,00 |

### 6.3. Visualizações e tabelas

| ID | Requisito | Prioridade | Critério de aceitação |
|---|---|---|---|
| RF-011 | **Lista de prioridades de reposição**: produto, categoria, fornecedor, estoque, nível, déficit, vendas no período, status e prioridade, do mais ao menos urgente | Must | Ordem igual à de CA-002 |
| RF-012 | Gráfico de **unidades vendidas por produto**, com cor = status do estoque e produtos sem vendas com zero | Must | Hanging Basket aparece com 0 |
| RF-013 | Gráfico de **produtos a repor por categoria** | Should | 5 categorias com 1 produto a repor cada |
| RF-014 | Quadro de **fornecedores dos produtos a repor**: nº de produtos, déficit total e e-mail (ausente = "não cadastrado") | Must | Ironwood Tools com "não cadastrado" |
| RF-015 | **Tabela de todos os produtos filtrados**, em seção expansível | Could | Mostra os 23 produtos ativos no padrão |
| RF-016 | **Notas** com o período usado, a exclusão de cancelados e a situação dos descontinuados (ocultos ou visíveis) | Should | Texto visível sob o título |

### 6.4. Situações sem dados

| ID | Requisito | Prioridade | Critério de aceitação |
|---|---|---|---|
| RF-017 | Filtros sem nenhum produto | Must | Indicadores 0 / US$ 0,00 e aviso "Nenhum produto encontrado para os filtros selecionados.", sem erro |
| RF-018 | Período sem pedidos | Must | Unidades e pedidos em aberto = 0, estoque inalterado e aviso "Sem vendas efetivas no período selecionado." |
| RF-019 | Nenhum produto a repor nos filtros | Must | Aviso "Nenhum produto precisa de reposição nos filtros selecionados." |
| RF-020 | Arquivo ausente, coluna faltando ou dado inválido | Must | Mensagem com o arquivo e o problema, sem nenhum indicador exibido |

### 6.5. Cenários de aceitação (base da Aula 1)

Salvo indicação, os cenários consideram os filtros padrão. A coluna "Verificado por" aponta os testes da SPEC.

| ID | Cenário | Resultado esperado | Requisitos | Verificado por |
|---|---|---|---|---|
| CA-001 | Abrir o dashboard | a repor **5** · zerados **1** · valor **US$ 4.731,00** · unidades **86** · em aberto **6** | RF-001 a RF-005 | TEST-011, TEST-013 |
| CA-002 | Lista de prioridades | P1: Hanging Basket, Tomato Seeds 'Roma', Hand Cultivator · P2: Pothos 'Golden' · P3: Orchid Food · Monitorar: Solar Lantern | RF-011, RN-005, RN-006 | TEST-011 |
| CA-003 | Pedido cancelado (nº 17, 1 Pruning Shears) | Pruning Shears com **1** unidade vendida (não 2) | RN-001 | TEST-004, TEST-011 |
| CA-004 | Ligar "Incluir descontinuados" | Bird Feeder "Descontinuado" / "Não repor" · a repor continua **5** · valor **US$ 4.763,00** | RF-010, RN-004 | TEST-011, TEST-013 |
| CA-005 | Categoria = Tools | a repor **1** · valor **US$ 448,50** · unidades **5** | RF-008 | TEST-011, TEST-013 |
| CA-006 | Fornecedor = RootWorks Supply (sem produtos) | indicadores zerados e aviso, sem erro | RF-017 | TEST-011, TEST-013 |
| CA-007 | Período 01/07/2024 a 31/07/2024 | unidades **0** · em aberto **0** · a repor **5** · valor **US$ 4.731,00** | RF-018, RN-007 | TEST-011, TEST-013 |
| CA-008 | Produto sem vendas (Hanging Basket) | aparece com **0** no gráfico e na lista | RF-012 | TEST-009, TEST-011 |
| CA-009 | Produto em vários pedidos (Fiddle-Leaf Fig, 4 pedidos) | valor do produto **US$ 252,00** (14 × 18), contado uma vez | RN-008 | TEST-008, TEST-011 |
| CA-010 | Ironwood Tools no quadro de fornecedores | e-mail "não cadastrado" | RF-014 | TEST-011 |
| CA-011 | `products.csv` ausente ou com coluna faltando | mensagem com o nome do arquivo e nenhum indicador | RF-020 | TEST-002, TEST-013 |

## 7. Requisitos não funcionais

| ID | Categoria | Requisito | Critério de verificação |
|---|---|---|---|
| RNF-001 | Confiabilidade | Dados inválidos geram mensagem clara e nenhum número parcial | TEST-002 e TEST-013 |
| RNF-002 | Integridade | Os arquivos de `data/raw/` nunca são alterados | TEST-003 (hash antes e depois) e `git diff --stat data/raw` vazio |
| RNF-003 | Manutenibilidade | Todas as regras ficam em funções puras testáveis, separadas da interface | Revisão: nenhuma fórmula em `app.py` |
| RNF-004 | Usabilidade | Lista de prioridades visível sem rolar a página em tela de 1500 × 1000 px. Textos em português | Conferência visual (print) |
| RNF-005 | Usabilidade | Nenhum elemento em vermelho (tema verde, sem `st.error`) | TEST-013 e conferência visual |
| RNF-006 | Desempenho | Tela carregada em menos de 3 segundos com a base da aula | Execução local: medido ≈ 2,3 s em 2026-11-01 (do acesso à página até os gráficos renderizados) |

## 8. Dados e integrações

- **Fontes de dados:** `products.csv`, `categories.csv`, `suppliers.csv`, `orders.csv`, `order_items.csv` e o dicionário `garden_shop_dicionario_dados.xlsx`, em `data/raw/`. O `customers.csv` é mantido, mas não é lido.
- **Entradas:** os CSVs e os filtros escolhidos na tela.
- **Saídas:** indicadores, tabelas e gráficos na tela. O app não grava arquivos.
- **Integrações:** nenhuma.
- **Dados sensíveis:** `customers.csv` tem nomes, e-mails e telefones de clientes. Por isso não é carregado nem exibido.
- **Retenção e descarte:** não se aplica (dados de exercício, somente leitura).

## 9. Regras de negócio

- **RN-001 (venda efetiva):** são os itens de pedidos com status `shipped`, `pending` ou `processing`. Pedidos `cancelled` nunca contam como venda.
- **RN-002 (tratamento dos status):** `shipped` = venda concluída e enviada. `pending` e `processing` = venda efetiva ainda não enviada: contam nas vendas (o cliente comprou) e no indicador de pedidos em aberto.
- **RN-003 (necessidade de reposição):** produto ativo, com nível de reposição > 0 e estoque ≤ nível. Usa "≤" porque, ao atingir o nível, a reposição já deve ser disparada.
- **RN-004 (descontinuados):** nunca recebem recomendação de reposição e nunca entram em RF-001 e RF-002. Ficam ocultos por padrão. Quando exibidos, aparecem como "Descontinuado" / "Não repor".
- **RN-005 (status do estoque):** Zerado (estoque = 0) · Crítico (≤ 50% do nível) · Abaixo do nível (> 50% e ≤ 100%) · Atenção (> 100% e ≤ 125%) · OK (> 125%) · Sem nível definido (nível = 0).
- **RN-006 (prioridade):** P1 Urgente = Zerado ou Crítico · P2 Alta = Abaixo do nível e vendas no período ≥ mediana · P3 Média = Abaixo do nível e vendas < mediana · Monitorar = Atenção. A mediana considera todos os produtos ativos, sem os filtros de categoria e fornecedor, para que a prioridade de um item não mude conforme o recorte.
- **RN-007 (período × posição atual):** o período filtra apenas pedidos. Estoque, valor, status e déficit vêm sempre da posição atual.
- **RN-008 (sem duplicação):** estoque e valor são contados uma vez por produto. As vendas são agregadas por produto antes de serem ligadas aos produtos.
- **RN-009 (déficit):** max(nível − estoque, 0). É o mínimo para voltar ao nível de referência, não uma sugestão de lote de compra.
- **RN-010 (dados preservados):** os arquivos originais são somente leitura.
- **RN-011 (cores):** o dashboard não usa vermelho.

## 10. Fluxos e exceções

### 10.1. Fluxo principal

O app carrega e valida os CSVs, monta a visão por produto (estoque atual e vendas do período), aplica os filtros e exibe os indicadores, a lista de prioridades, os gráficos e o quadro de fornecedores.

### 10.2. Fluxos alternativos

- **Incluir descontinuados:** Bird Feeder entra nas tabelas e no valor do estoque, mas nunca em "a repor".
- **Só uma data escolhida no período:** o período vale para aquele dia.
- **Data inicial maior que a final:** as datas são invertidas.
- **Filtros sem produtos, período sem vendas ou nada a repor:** avisos de RF-017 a RF-019.

### 10.3. Tratamento de erros

Arquivo ausente, coluna faltando, chave duplicada ou órfã, status desconhecido, data fora do formato `AAAA-MM-DD` ou número inválido: o app mostra um aviso no formato "Não foi possível carregar os dados: `<arquivo>`: `<problema>`" e não exibe nenhum indicador (RF-020). Os casos estão detalhados na SPEC, seção 7.2.

## 11. Experiência e interface

- **Plataforma:** web local (Streamlit), em http://localhost:8501.
- **Referências visuais:** protótipo da Aula 1 (filtros, cartões, gráficos e lista de prioridades).
- **Acessibilidade:** a cor do status sempre vem acompanhada do texto do status. A paleta não depende de vermelho e verde lado a lado.
- **Estados da interface:** carregando (spinner padrão) · sucesso · vazio (RF-017 a RF-019) · erro de dados (RF-020, em amarelo).
- **Compatibilidade:** navegadores modernos (Chrome, Edge, Firefox) e Windows, macOS ou Linux com Python 3.10+.

## 12. Riscos e dependências

| Risco ou dependência | Impacto | Mitigação |
|---|---|---|
| Amostra pequena (23 pedidos válidos): rankings e a mediana mudam com um único pedido | Médio | Prioridade baseada principalmente no estoque. A mediana só separa P2 de P3 |
| Produto sem vendas por estar em falta (Hanging Basket): demanda reprimida invisível | Médio | Fica como P1 por estar zerado. A limitação está registrada na SPEC |
| Dicionário diz datas `DD/MM/AAAA`, arquivos usam `AAAA-MM-DD` | Médio | A carga segue o arquivo e rejeita outros formatos (SPEC, ADR-004) |
| Níveis de reposição possivelmente altos para o ritmo de vendas | Baixo | O dashboard respeita o nível cadastrado. A revisão fica como pendência para a loja (DP-001) |
| Dependência de Streamlit, pandas e Altair | Baixo | Versões mínimas em `requirements.txt` |

## 13. Entregáveis

- Dashboard Streamlit (`app.py` e o pacote `garden_dashboard/`).
- `PRD.md`, `SPEC.md` e `AGENTS.md`.
- Testes automatizados (`tests/`) com recorte manual dos CSVs.
- Procedimento de instalação, execução e testes em `AGENTS.md`.
- Print do dashboard em execução.

## 14. Critérios de conclusão do produto

O produto estará pronto quando:

- Os requisitos Must estiverem implementados. ✅
- Os cenários CA-001 a CA-011 estiverem verificados. ✅ (TEST-011 e TEST-013)
- Os testes estiverem passando. ✅ (`pytest`: 66 testes)
- PRD, SPEC e AGENTS estiverem coerentes com o código. ✅
- Os riscos críticos estiverem tratados. ✅
- O procedimento de execução estiver validado. ✅ (ver AGENTS.md §6)

## 15. Relação com os documentos técnicos

- **Especificação de referência:** `SPEC.md`
- **Instruções gerais para agentes:** `AGENTS.md`
- **Instruções para Claude Code:** este projeto não usa `CLAUDE.md`. O `AGENTS.md` vale para qualquer agente.

## 16. Decisões pendentes

| ID | Questão | Responsável | Status |
|---|---|---|---|
| DP-001 | Revisar os níveis de reposição que parecem altos para o ritmo de vendas (ex.: Tomato Seeds, nível 40 e 4 vendas em 5 meses) | Gestão da loja | Pendente (fora do escopo do dashboard) |
| DP-002 | Confirmar com a gestão os limites de 50% e 125% de RN-005 | Gestão da loja | Pendente. Valores adotados como proposta |
| DP-003 | Passar a registrar movimentações de estoque e prazos de entrega, para permitir ponto de pedido e previsão no futuro | Gestão da loja | Pendente (próxima versão) |

## 17. Histórico de alterações

| Versão | Data | Alteração |
|---|---|---|
| 1.0 | 2026-11-01 | Criação inicial a partir da proposta da Aula 1. Escopo revisado: removidos a cobertura em meses, a simulação com pedidos em aberto e o filtro de status. Incluídos o status "Sem nível definido" e a mediana sem filtros na prioridade |
| 1.1 | 2026-11-01 | Contagem de elementos visuais corrigida. Critérios passam a indicar onde são testados |
| 2.0 | 2026-11-01 | Documento reorganizado no modelo da Aula 2 (`templates/PRD.md` do repositório da disciplina): IDs com 3 dígitos (RF-001, RN-001, CA-001), RNFs, jornada, riscos e decisões pendentes. **Nenhuma regra ou número mudou** |
