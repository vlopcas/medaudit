# ADR-029: catálogos de grafo exigem admissão fail-closed

## Status

Aceita para avaliação sintética.

## Contexto

O gateway explícito passou no holdout quando recebeu um grafo previamente
revisado. O risco seguinte está antes do traversal: candidatos de entidades e
relações podem conter referências ambíguas, arestas órfãs, provenance ausente ou
vocabulário não autorizado.

Construir diretamente modelos executáveis a partir desses candidatos faria as
invariantes locais falharem tarde demais e misturaria defeitos estruturais com
pendências de revisão.

## Decisão

- representar candidatos em um draft não executável;
- auditar o draft antes de construir `GraphEntity` ou `GraphEdge` confiáveis;
- rejeitar defeitos estruturais e provenance ausente;
- encaminhar ambiguidade, relação desconhecida e duplicidade para revisão;
- aplicar precedência de rejeição quando erros e revisões coexistirem;
- materializar `InMemoryKnowledgeGraph` somente quando não houver achados;
- manter uma allowlist explícita de relações;
- exigir holdout sintético antes de promover a fronteira.

## Consequências

Nenhum processo de extração futuro poderá alimentar traversal diretamente. Ele
deverá produzir candidatos e atravessar esta fronteira ou uma sucessora com as
mesmas garantias.

A decisão não aprova extração, resolução automática de revisão, persistência ou
uso de entidades reais. Esses temas exigem avaliações próprias.
