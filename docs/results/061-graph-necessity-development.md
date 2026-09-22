# Resultado 061: benchmark de necessidade de grafo

## Hipótese

Casos relacionais sintéticos permitiriam distinguir capacidades já cobertas por
BM25, planejamento ou regras de lacunas candidatas a traversal em grafo.

## Estratégia e dataset

O benchmark executa componentes reais do projeto:

- BM25 sobre pequenos corpora sintéticos por caso;
- roteador e planejador determinísticos para comparação explícita;
- motor de regras para uma decisão temporal formalizável.

Uma lacuna candidata exige simultaneamente uma cadeia esperada, ausência da
cadeia completa no top-k lexical, ausência de regra aplicada e ausência de plano
explícito pronto. Casos sem caminho e entidade ambígua não são marcados como
lacuna automaticamente, pois exigem abstention ou revisão, não mais retrieval.

O dataset `graph_necessity_development.json`, política
`graph-necessity-development-v1`, contém oito casos integralmente sintéticos:
dois a quatro saltos, supersessão temporal, impacto reverso, ausência de caminho,
ambiguidade e comparação explícita. Seu SHA-256 é
`cb5ffecb0af2bbdecb4da9b9eac113d9016400f2da76ae4e8e48a4cec3ded3d6`.

```bash
docker compose run --rm evaluate-graph-necessity
```

## Resultado

- BM25 recuperou a cadeia completa em 1/6 casos relacionais (16,7%);
- o conjunto de baselines resolveu 2/6 (33,3%): comparação explícita pelo
  planner e decisão temporal pelo motor de regras;
- restaram quatro lacunas candidatas: dois saltos, três saltos, quatro saltos e
  impacto reverso;
- ausência de caminho e entidade ambígua permaneceram fora da contagem de ganho;
- 290 testes passaram; Ruff e mypy passaram em 201 arquivos.

## Limitações

Os corpora são pequenos e isolados, o top-k varia conforme o tamanho da cadeia e
o benchmark mede recuperação de evidência, não qualidade de resposta. Uma falha
lexical não prova que grafo seja a melhor solução; apenas satisfaz o gate para
comparar um protótipo controlado.

## Decisão

Está autorizado um protótipo determinístico de grafo em memória, sem nova
dependência, com:

- entidades identificadas por IDs exatos;
- arestas sintéticas previamente revisadas;
- traversal limitado a quatro saltos;
- documento e chunk de origem em cada aresta;
- estados explícitos para caminho ausente e entidade ambígua.

O protótipo será comparado no mesmo dataset. Graph RAG completo, extração
automática, entity resolution probabilística, banco de grafo e corpus privado
continuam bloqueados.

O primeiro teste do componente foi registrado no
[Resultado 062](062-graph-traversal-development.md). Ele reproduziu as categorias
em um fixture próprio e revelou que a comparação no mesmo input ainda depende
de uma fronteira explícita de resolução de entidades e montagem do traversal.
