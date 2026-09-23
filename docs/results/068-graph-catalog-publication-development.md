# Resultado 068: publicação versionada de catálogo de grafo

## Hipótese

Uma fronteira determinística publicaria somente grafos admitidos, produziria
snapshots reproduzíveis e bloquearia mudanças destrutivas não revisadas ou
revisões vinculadas ao snapshot errado.

## Estratégia e dataset

`PublishedGraphCatalog` ordena entidades e arestas e calcula um SHA-256 sobre:

- versão monotônica;
- identificador do snapshot anterior;
- conteúdo integral das entidades;
- relações e provenance integral das arestas.

A versão inicial deve ser `1` e cada publicação posterior deve incrementar uma
unidade. Adições são não destrutivas. Remoção ou mutação de entidade e remoção ou
alteração de uma aresta exigem referências exatas de mudança e o identificador
do snapshot anterior.

O dataset `graph_catalog_publication_development.json`, política
`graph-catalog-publication-development-v1`, contém dez casos integralmente
sintéticos. Seu SHA-256 é
`83cba8cd30af2075b8a4730b162a50e9315285abcd953f1b77c3d96d48b06b84`.

```bash
docker compose run --rm evaluate-graph-catalog-publication
```

## Resultado

- 10/10 publicações corresponderam ao esperado;
- publicação inicial e atualização aditiva foram aceitas;
- catálogo não admitido e versões inválidas não foram publicados;
- remoção revisada e vinculada ao snapshot anterior foi publicada;
- remoção pendente, mutação de entidade e mudança de provenance ficaram em
  revisão;
- referência de mudança obsoleta foi recusada;
- 331 testes passaram; Ruff passou e mypy não encontrou problemas em 223
  arquivos.

## Limitações

O snapshot identifica o conteúdo efetivamente publicado, mas ainda não inclui a
identidade da política de relações usada na admissão. Assim, o mesmo conteúdo
poderia ser admitido sob allowlists diferentes sem que essa decisão de
governança aparecesse no snapshot.

Persistência, concorrência, assinatura, extração e dados privados continuam fora
do escopo.

## Decisão

A fronteira de publicação é válida em desenvolvimento, mas ainda não deve seguir
para holdout. O próximo incremento deve vincular uma identidade determinística
da política de relações à admissão e ao snapshot publicado. Somente depois dessa
composição será preparado um holdout sintético inédito.
