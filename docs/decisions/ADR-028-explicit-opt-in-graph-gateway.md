# ADR-028: gateway de grafo é explícito e opt-in

## Status

Aceita para avaliação sintética.

## Contexto

Traversal e compilação de solicitações passaram isoladamente em desenvolvimento.
A composição posterior recuperou quatro cadeias relacionais que o BM25 não
completou no mesmo slice sintético, preservando provenance e os estados fechados
dos controles.

O grafo, contudo, foi fornecido já revisado e as perguntas continham dois
endpoints explícitos. O resultado não sustenta roteamento amplo nem Graph RAG.

## Decisão

- introduzir `ExplicitGraphGateway` apenas como fronteira experimental;
- ativar o gateway somente para intenção de caminho e duas referências únicas;
- manter `not_applicable`, `review` e `no_path` como resultados distintos;
- limitar traversal a quatro saltos e exigir provenance por aresta;
- manter BM25 como caminho padrão para consultas fora da gramática explícita;
- exigir holdout sintético congelado antes de qualquer promoção adicional;
- não conectar extração documental, catálogo privado, LLM ou banco de grafo.

## Consequências

O projeto passa a testar graph-assisted retrieval sem ampliar silenciosamente o
escopo do roteador. Consultas implícitas continuam com os componentes existentes
ou pedem esclarecimento; o gateway não infere endpoints ausentes.

Mesmo um holdout aprovado validará apenas esta fronteira estreita. Construção e
governança do grafo, respostas finais e custo operacional exigirão gates
independentes.

## Resultado posterior

O holdout congelado do
[Resultado 065](../results/065-graph-assisted-retrieval-holdout.md) atingiu 8/8,
com quatro cadeias e quatro controles corretos. O gateway fica aprovado como
componente estreito e opt-in sobre relações revisadas. As demais restrições
desta decisão permanecem vigentes.
