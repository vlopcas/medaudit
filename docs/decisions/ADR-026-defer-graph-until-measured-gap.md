# ADR-026: grafo é adiado até existir uma lacuna multi-hop medida

## Status

Aceita.

## Contexto

O ciclo de regras estruturadas validou resolução, auditoria, admissão e
publicação em dados sintéticos. O pipeline também possui roteamento e
decomposição para sinais explícitos. Esses resultados não provam capacidade
multi-hop geral, mas tampouco demonstram que um grafo seja necessário.

## Decisão

- não adicionar Graph RAG, banco de grafo ou ETL relacional neste momento;
- criar primeiro um benchmark sintético de necessidade de grafo;
- executar os baselines atuais no benchmark antes de construir um protótipo;
- tratar entity resolution como pré-requisito separado;
- autorizar protótipo somente diante de falha relacional reproduzível;
- comparar qualquer protótipo contra os mesmos casos, métricas e políticas de
  provenance, temporalidade e abstention;
- remover ou não promover o grafo se ele não justificar sua complexidade.

## Consequências

O estudo de Knowledge Graph continua no roteiro, mas sua implementação passa a
ter um gate empírico. O próximo artefato é um dataset sintético de
desenvolvimento, não um grafo e não um holdout. Corpus privado, entidades reais e
serviços externos permanecem fora do escopo.

## Resultado posterior

O [Resultado 061](../results/061-graph-necessity-development.md) encontrou quatro
falhas relacionais candidatas após executar os baselines atuais. A condição para
um protótipo foi atendida. Está autorizado somente um traversal determinístico
em memória, sem dependência de banco, para comparação no mesmo desenvolvimento.

O [Resultado 062](../results/062-graph-traversal-development.md) validou a
primitiva em um fixture sintético próprio. Como os IDs foram fornecidos já
resolvidos, a comparação integrada continua pendente e o escopo permanece
limitado pela [ADR-027](ADR-027-bounded-reviewed-graph-traversal.md).
