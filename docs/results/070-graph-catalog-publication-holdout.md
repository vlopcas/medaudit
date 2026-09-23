# Resultado 070: holdout da publicação de catálogo de grafo

## Objetivo

Verificar em casos sintéticos inéditos se a publicação completa preserva
admissão fail-closed, versionamento monotônico, revisão de mudanças governadas e
identidade versionada da política de relações.

## Congelamento

O dataset `graph_catalog_publication_holdout.json` contém oito casos totalmente
sintéticos sob a política `graph-catalog-publication-holdout-v1`.

Hash congelado e observado:

```text
ccef8a9130d6a5ab5da67dde1c70512a2d618c9ee0111e054005ab607dff49bb
```

Antes da abertura, a configuração Compose foi validada, a imagem foi construída
e passaram 337 testes, Ruff e mypy em 223 arquivos. O serviço exige o hash acima,
grava somente um artefato local ignorado e recusa sobrescrita.

## Execução única

```bash
docker compose run --rm evaluate-graph-catalog-publication-holdout
```

O holdout foi executado uma única vez após o commit de congelamento `bc2600a`.

## Resultado

- 8/8 casos corresponderam exatamente ao esperado;
- publicação inicial e atualização puramente aditiva foram aceitas;
- catálogo não admitido e salto de versão não foram publicados;
- troca de política sem revisão permaneceu em revisão;
- troca de política revisada e vinculada ao snapshot anterior foi publicada;
- mudança simultânea de política, entidade e aresta apresentou exatamente três
  pendências;
- revisão vinculada a snapshot obsoleto foi recusada;
- o hash observado correspondeu ao hash congelado.

## Decisão

A publicação de catálogos de grafo está validada no escopo sintético atual. O
holdout está encerrado e não será reutilizado para ajuste.

Isso não aprova extração automática, persistência, concorrência, corpus privado,
Graph RAG como arquitetura final nem integração ao runtime padrão. O próximo
gate deve ser escolhido a partir do roadmap arquitetural, sem ampliar o grafo
apenas por disponibilidade do componente.
