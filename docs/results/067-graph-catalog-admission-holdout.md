# Resultado 067: holdout da admissão de catálogo de grafo

## Hipótese congelada

A política de admissão manteria comportamento fail-closed em combinações
sintéticas inéditas, preservando precedência de erros estruturais sobre
pendências de revisão e materializando somente catálogos limpos.

## Protocolo

O dataset `graph_catalog_admission_holdout.json`, política
`graph-catalog-admission-holdout-v1`, foi congelado antes da execução no commit
`94f65cb`. Seu SHA-256 é
`7d7a8de3eb97603370a864257e13f3b5aa9d6de3a3eda2f201b41b0f5b5345f7`.

Os oito casos integralmente sintéticos cobrem:

- catálogo limpo com múltiplas arestas;
- catálogo limpo com entidades desconectadas;
- colisão entre ID e alias;
- colisão entre IDs que diferem apenas por caixa;
- múltiplas pendências de revisão;
- aresta órfã combinada a relação desconhecida;
- ID duplicado combinado a alias ambíguo;
- múltiplos erros estruturais na mesma aresta.

O serviço verifica o hash, grava o relatório local ignorado
`artifacts/graph-catalog-admission-holdout.local.json` e recusa sobrescrita. Os
prechecks anteriores à abertura passaram com 320 testes, Ruff e mypy em 219
arquivos.

```bash
docker compose run --rm evaluate-graph-catalog-admission-holdout
```

## Resultado

- correspondência exata: 8/8;
- dois catálogos limpos foram admitidos e materializados;
- três combinações estruturalmente inválidas foram rejeitadas;
- três combinações não bloqueantes permaneceram em revisão;
- erros estruturais prevaleceram quando coexistiram com revisão;
- hash observado igual ao hash congelado.

## Limitações

O holdout avalia candidatos já estruturados e uma allowlist fornecida em tempo
de execução. Ele não cobre publicação, versionamento, diff entre catálogos,
retirada de entidades, extração documental ou correção humana dos achados.

## Decisão

A admissão fail-closed de catálogos de grafo está validada para o escopo
sintético atual. O holdout está encerrado e não será usado para tuning.

O próximo gate será uma fronteira de publicação versionada que aceite somente
catálogos admitidos, produza identidade determinística e exija revisão para
mudanças destrutivas. Extração automática, banco de grafo e corpus privado
continuam bloqueados.
