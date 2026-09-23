# ADR-031: política de relações do grafo tem identidade versionada

## Status

Aceita para desenvolvimento sintético.

## Contexto

A publicação versionada já identificava conteúdo, provenance, versão e snapshot
anterior. Porém, a allowlist usada pela admissão não participava dessa
identidade. O mesmo grafo poderia, portanto, ser publicado sob decisões de
governança diferentes sem que o snapshot tornasse essa diferença verificável.

## Decisão

- representar a política de relações por nome, versão positiva e conjunto não
  vazio de relações permitidas;
- calcular seu identificador por SHA-256 sobre uma serialização canônica desses
  três campos;
- anexar o identificador a todo resultado de admissão, inclusive rejeição e
  revisão;
- incluir o identificador no conteúdo autenticado pelo identificador de
  publicação;
- tratar qualquer troca de política entre snapshots como mudança governada que
  exige revisão exata vinculada à publicação anterior;
- preservar datasets de holdout já congelados, derivando para eles uma política
  nomeada a partir da versão da avaliação.

## Consequências

Dois snapshots com as mesmas entidades e arestas, mas políticas diferentes,
possuem identidades diferentes. Uma troca de política não pode passar como
atualização silenciosa. O contrato permanece em memória e ainda não aprova
persistência, extração automática, corpus privado ou uso no runtime padrão.

Com essa composição validada em desenvolvimento, o próximo gate pode ser um
holdout sintético inédito da publicação completa.

## Resultado posterior

O holdout do [Resultado 070](../results/070-graph-catalog-publication-holdout.md)
atingiu 8/8 e validou a decisão no escopo sintético atual.
