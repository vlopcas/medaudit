# Checkpoint arquitetural 001: regras para grafo

## Pergunta

Após concluir o ciclo de regras estruturadas, existe evidência de que um grafo é
necessário para o próximo incremento?

## Capacidades observadas

| Necessidade | Menor componente atual | Evidência | Situação |
|---|---|---|---|
| Resolver regra por vigência, condição e prioridade | motor determinístico | [Resultado 053](../results/053-structured-rules-development.md) | Coberta no desenvolvimento sintético |
| Bloquear conflito e redundância não revisada | auditoria e admissão | [Resultado 056](../results/056-structured-rule-admission-holdout.md) | Coberta no holdout sintético |
| Preservar versões, substituições e aposentadorias | fronteira de publicação | [Resultado 059](../results/059-structured-rule-publication-holdout.md) | Coberta no holdout sintético |
| Rotear comparação explícita e dependência externa | roteador determinístico | [Resultado 009](../results/009-explicit-query-routing-holdout.md) | Coberta no slice sintético explícito |
| Executar passos temporais por documento | executor de decomposição | [Resultado 011](../results/011-decomposition-execution-holdout.md) | Coberta no slice sintético explícito |
| Preservar contexto e citações por grupo | agregador de evidências | [Resultado 012](../results/012-evidence-aggregation-holdout.md) | Coberta no slice sintético avaliado |

Esses resultados não demonstram que relações multi-hop arbitrárias estejam
resolvidas. Também não demonstram que estejam falhando. A heurística ampla de
detecção estrutural foi rejeitada no [Resultado 008](../results/008-structural-decomposition-holdout.md),
mas isso é uma falha de classificação por superfície textual, não evidência de
que armazenamento ou retrieval em grafo a corrigiria.

## Lacunas candidatas

Um grafo só será considerado para perguntas cuja resposta dependa de uma cadeia
relacional explícita, por exemplo:

- regra → exceção → condição → outra regra;
- regra substituída → regra substituta → documento de origem;
- procedimento → regras diretas e indiretas que o afetam;
- impacto reverso: quais decisões dependem de uma condição alterada;
- ausência de caminho entre duas entidades, que deve produzir resultado vazio e
  não uma associação inventada.

Resolução de entidades ambíguas é um pré-requisito separado. Um grafo não deve
ser usado para mascarar aliases ou entidades não resolvidas.

## Decisão

Graph RAG fica adiado. Não há, neste momento, uma lacuna medida que justifique
ETL de entidades e relações, armazenamento, traversal e operação adicionais.
Isso não remove Knowledge Graph do plano de estudos; apenas exige evidência antes
da implementação.

O próximo experimento será um benchmark sintético de necessidade de grafo. Ele
avaliará primeiro BM25, decomposição explícita e regras estruturadas sobre os
mesmos casos, sem implementação de grafo.

## Gate para autorizar um protótipo

O benchmark deve conter casos inéditos de:

- cadeia com dois, três e quatro saltos;
- supersessão temporal;
- exceção e condição compartilhada;
- impacto reverso;
- entidades desconectadas;
- entidade ambígua que exige revisão.

Um protótipo de grafo só será autorizado se houver falha reproduzível em pelo
menos uma categoria relacional que não seja explicada por parsing, entity
resolution, ausência de evidência ou regra formalizável. Se autorizado, deverá
ser comparado na mesma avaliação e permanecer somente se:

- melhorar a recuperação da cadeia completa no slice que motivou o experimento;
- não reduzir correção temporal nem abstention em casos sem caminho;
- preservar documento de origem em cada nó ou aresta recuperada;
- tornar explícitos custo de ETL, latência e complexidade operacional.

Até esse gate, nenhuma dependência ou banco de grafo será adicionado.

## Resultado do gate

O benchmark foi executado posteriormente no
[Resultado 061](../results/061-graph-necessity-development.md). BM25 recuperou a
cadeia completa em 1/6 casos relacionais, e regras ou planejamento elevaram a
resolução combinada para 2/6. Restaram quatro lacunas candidatas nas categorias
de dois, três e quatro saltos e impacto reverso.

O gate autoriza um protótipo determinístico em memória, limitado a relações
sintéticas revisadas. Ele não autoriza Graph RAG completo, banco de grafo,
extração automática de relações nem corpus privado.

## Resultado do protótipo

O [Resultado 062](../results/062-graph-traversal-development.md) recuperou as
quatro categorias candidatas, preservou provenance por aresta e manteve os
controles de caminho ausente e ambiguidade. A travessia em si demonstrou valor
no fixture do componente.

O protótipo, porém, recebeu entidades já resolvidas e não foi executado sobre o
mesmo input textual do BM25. A promoção continua bloqueada até avaliar a
fronteira pergunta-entidade-traversal e fazer uma comparação integrada. A
decisão estreita está registrada na
[ADR-027](../decisions/ADR-027-bounded-reviewed-graph-traversal.md).

A primeira fronteira pergunta-entidade atingiu 10/10 no
[Resultado 063](../results/063-explicit-graph-request-development.md). Ela só
compila intenção explícita com duas referências revisadas; os demais casos não
se aplicam ou seguem para revisão. O próximo gate é a composição completa e a
comparação com BM25 nos mesmos inputs.
