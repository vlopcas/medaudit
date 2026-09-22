# Resultado 060: checkpoint arquitetural da Fase 9

## Objetivo

Decidir se o encerramento do ciclo de regras estruturadas já fornece evidência
suficiente para iniciar Graph RAG.

## Evidência considerada

- motor de regras: 8/8 em desenvolvimento sintético;
- admissão de catálogos: 6/6 em holdout congelado;
- publicação versionada: 8/8 em holdout congelado;
- roteamento explícito: 15/15 em holdout;
- execução de decomposição: 10/10 casos e 17/17 documentos por passo;
- agregação de evidências: 4/4 casos e 7/7 citações preservadas;
- detecção estrutural ampla: rejeitada com 62,5% e 37,5% de falsos positivos.

## Interpretação

As capacidades formalizáveis e os fluxos multi-documento explícitos possuem
baselines menores que um grafo. A falha da heurística ampla não isola traversal
relacional como causa e, portanto, não justifica Graph RAG.

Não existe ainda um benchmark de cadeias relacionais, impacto reverso, ausência
de caminho e ambiguidade de entidade. Sem essa avaliação, qualquer ganho de
grafo seria presumido.

## Decisão

O checkpoint foi concluído com decisão de **adiar Graph RAG**. O próximo passo é
criar um benchmark sintético de necessidade de grafo e executar primeiro os
baselines existentes. Um protótipo só será autorizado se surgir uma falha
relacional reproduzível que os componentes menores não resolvam.

Os critérios completos estão no
[Checkpoint arquitetural 001](../architecture-checkpoints/001-phase-9-rules-to-graph.md)
e a decisão está no
[ADR-026](../decisions/ADR-026-defer-graph-until-measured-gap.md).
