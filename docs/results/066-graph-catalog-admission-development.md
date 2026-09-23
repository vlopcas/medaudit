# Resultado 066: admissão de catálogo de grafo

## Hipótese

Uma fronteira determinística impediria que candidatos malformados ou não
revisados se tornassem um grafo executável, preservando separação explícita
entre rejeição estrutural e revisão humana.

## Estratégia e dataset

`GraphCatalogDraft` recebe entidades e arestas ainda não confiáveis. A auditoria
classifica como erro bloqueante:

- catálogo sem entidades;
- ID de entidade duplicado ou campo obrigatório vazio;
- aresta órfã ou autorreferente;
- campo de relação ou provenance vazio.

Colisões de referência sem distinção de caixa, relações fora da allowlist e
arestas semanticamente duplicadas exigem revisão. Somente um catálogo sem
achados é convertido em `InMemoryKnowledgeGraph`.

O dataset `graph_catalog_admission_development.json`, política
`graph-catalog-admission-development-v1`, contém dez casos integralmente
sintéticos. Seu SHA-256 é
`1d964345bc342452ce99dd42b7180554710c6f14f731cb50016e50ce1a3afdaf`.

```bash
docker compose run --rm evaluate-graph-catalog-admission
```

## Resultado

- 10/10 admissões corresponderam ao esperado;
- o catálogo limpo foi o único convertido em grafo executável;
- seis classes malformadas foram rejeitadas;
- alias ambíguo, relação desconhecida e duplicidade semântica foram mantidos em
  revisão;
- 318 testes passaram; Ruff passou e mypy não encontrou problemas em 219
  arquivos.

## Limitações

A fronteira audita candidatos já estruturados. Ela não extrai entidades ou
relações, não determina se uma afirmação documental é verdadeira e não resolve
automaticamente achados de revisão. A allowlist de relações é fornecida pelo
chamador e ainda não possui publicação ou versionamento próprios.

## Decisão

A admissão fail-closed pode avançar para um holdout sintético inédito. O próximo
passo é congelar casos combinados e adversariais, incluindo precedência de erro
sobre revisão, colisões entre ID e alias e múltiplos achados.

Extração automática, catálogo privado, persistência e Graph RAG continuam
bloqueados.
