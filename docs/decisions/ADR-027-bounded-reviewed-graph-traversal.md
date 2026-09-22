# ADR-027: traversal em grafo permanece limitado e revisado

## Status

Aceita.

## Contexto

O benchmark de necessidade encontrou quatro lacunas relacionais candidatas nos
baselines atuais. Um protótipo em memória recuperou as cadeias sintéticas de
dois, três e quatro saltos e de impacto reverso, preservando a origem de cada
aresta e falhando fechado diante de alias ambíguo.

Esse teste parte de IDs já resolvidos. Ele não demonstra que perguntas livres
podem ser convertidas com segurança em entidades, relações e direção de busca.

## Decisão

- manter o grafo como componente experimental, determinístico e em memória;
- aceitar somente entidades e relações previamente revisadas;
- limitar traversal a quatro saltos e preservar provenance por aresta;
- encaminhar referência ausente ou ambígua para revisão;
- não adicionar banco de grafo, extração automática ou corpus privado;
- avaliar entity resolution e construção da solicitação antes da integração com
  retrieval;
- exigir comparação integrada sobre os mesmos casos antes de promover
  recuperação assistida por grafo.

## Consequências

O projeto passa a ter uma primitiva testável para relações multi-hop sem assumir
o custo operacional de Graph RAG. O próximo risco deixa de ser a travessia e
passa a ser a ligação auditável entre linguagem natural e IDs revisados.

Um acerto no fixture do componente não deve ser relatado como ganho ponta a
ponta. Holdout, banco de grafo, ETL documental e uso de dados privados continuam
bloqueados.

## Resultado posterior

O [Resultado 063](../results/063-explicit-graph-request-development.md) validou
uma gramática conservadora para compilar solicitações. Ela atende ao
pré-requisito inicial de entity resolution explícita, mas ainda não substitui a
comparação integrada exigida por esta decisão.
