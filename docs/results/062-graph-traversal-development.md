# Resultado 062: traversal determinístico em grafo

## Hipótese

Um grafo pequeno, em memória e composto somente por entidades e relações
revisadas recuperaria as quatro categorias de lacuna do benchmark anterior sem
inventar caminhos, ocultar ambiguidade ou perder a origem das relações.

## Estratégia e dataset

O protótipo usa busca em largura determinística, nos sentidos direto ou reverso,
com limite estrito de um a quatro saltos. IDs e aliases são resolvidos por
igualdade exata. Referência ausente ou ambígua produz `review`; entidades
desconectadas produzem `no_path`. Cada aresta exige documento e chunk de origem.

O dataset `graph_traversal_development.json`, política
`graph-traversal-development-v1`, contém oito casos integralmente sintéticos. Seu
SHA-256 é
`80d5a2737f715d06556e3d851bf31fd25d118a4317e253102e48371e6c5b33e7`.

```bash
docker compose run --rm evaluate-graph-traversal
```

## Resultado

- 8/8 casos corresponderam exatamente ao resultado esperado;
- as quatro categorias candidatas — dois, três e quatro saltos e impacto
  reverso — foram recuperadas (4/4);
- todas as arestas dos caminhos retornados conservaram provenance;
- ausência de caminho resultou em `no_path` e alias ambíguo resultou em
  `review`;
- 296 testes passaram; Ruff passou e mypy não encontrou problemas em 207
  arquivos.

## Limitações

O avaliador fornece ao traversal as referências inicial e final já resolvidas.
Ele não interpreta perguntas livres, não extrai entidades ou relações e não
recupera o grafo a partir de documentos. O dataset reproduz as categorias do
benchmark de necessidade, mas é um fixture próprio do componente; portanto,
este resultado ainda não é uma comparação integrada no mesmo input do BM25.

Latência, custo de ETL, atualização, escala e desempenho sobre corpus privado
também não foram medidos.

## Decisão

O traversal permanece como componente experimental estreito. O ganho demonstra
que relações revisadas resolvem as quatro cadeias candidatas, mas não justifica
Graph RAG, banco de grafo ou extração automática.

O próximo gate deve testar a fronteira entre pergunta e grafo: resolução
determinística de entidades e montagem explícita de uma solicitação de
traversal. Depois disso, uma avaliação integrada deve comparar BM25 e recuperação
assistida por grafo sobre os mesmos casos antes de qualquer holdout ou conexão
ao catálogo privado.
