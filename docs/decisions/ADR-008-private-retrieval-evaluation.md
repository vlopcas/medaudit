# ADR-008: Avaliação privada de retrieval antes de embeddings

## Status

Aceita em 2026-09-08.

## Contexto

O corpus processado está pronto para busca, mas adotar embeddings sem um golden
set impediria saber se a complexidade trouxe ganho. Perguntas, julgamentos de
relevância e resultados por caso também podem revelar informações privadas.

## Decisão

Avaliar primeiro BM25 sobre os chunks privados. O golden set local declara uma
data de referência e permite relevância no nível de documento ou de chunk, mas
nunca ambos no mesmo caso. Casos sem referências medem abstention.

O avaliador exige que a data do golden set corresponda à materialização,
rejeita referências desconhecidas e grava detalhes somente em um arquivo
`.local.json`. O terminal mostra métricas agregadas e nunca perguntas, conteúdo
identificadores recuperados ou nomes de categorias.

## Consequências

- a primeira rotulagem pode ser feita no nível de documento;
- relevância de chunks pode ser adicionada gradualmente;
- Hit Rate, Recall, MRR e abstention formam a baseline comparável;
- `top_k` e limiar mínimo de score precisam ser registrados por experimento;
- embeddings só serão justificáveis se superarem essa baseline no mesmo set.

## Como validar

- testar relevância por documento e por chunk;
- rejeitar níveis misturados, IDs desconhecidos e datas incompatíveis;
- provar que relatório e terminal não contêm perguntas;
- manter golden set e relatório reais ignorados pelo Git.
