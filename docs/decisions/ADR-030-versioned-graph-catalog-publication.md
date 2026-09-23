# ADR-030: publicação do grafo é versionada e encadeada

## Status

Aceita para desenvolvimento sintético.

## Contexto

A admissão fail-closed passou no holdout, mas um grafo admitido ainda era apenas
um objeto em memória. Uso auditável exige identidade de snapshot, sequência de
versões e revisão explícita para alterações que removam ou mudem conhecimento
publicado.

## Decisão

- publicar somente resultados de admissão com status `admitted`;
- ordenar entidades e arestas antes de calcular identidade;
- incluir versão, snapshot anterior, conteúdo e provenance no SHA-256;
- iniciar na versão `1` e exigir incremento unitário;
- permitir adições provenientes de catálogo admitido;
- tratar remoções, mutações e alterações de provenance como destrutivas;
- exigir revisão exata vinculada ao snapshot anterior;
- recusar referências de mudança obsoletas;
- não abrir holdout até vincular também a política de relações ao snapshot.

## Consequências

O histórico publicado forma uma cadeia determinística e mudanças silenciosas
não chegam ao traversal. A publicação continua em memória e não implica banco
de grafo ou integração ao runtime padrão.

A identidade da allowlist de relações permanece um pré-requisito explícito para
o próximo gate.
