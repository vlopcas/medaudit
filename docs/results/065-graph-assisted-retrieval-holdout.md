# Resultado 065: holdout da recuperação assistida por grafo

## Hipótese congelada

O gateway explícito manteria, em casos sintéticos inéditos, a recuperação de
cadeias multi-hop observada no desenvolvimento, sem inventar caminhos nem ativar
grafo para consultas fora do escopo.

## Protocolo

O dataset `graph_assisted_retrieval_holdout.json`, política
`graph-assisted-retrieval-holdout-v1`, foi congelado antes da execução no commit
`e3ba6b3`. Seu SHA-256 é
`d395bdcb5bd3c3e4aad6d74cc418597247d98acbfb1ad449cb8ab06abb0c75f7`.

O conjunto contém oito casos integralmente sintéticos:

- quatro cadeias inéditas de dois, três e quatro saltos e impacto reverso;
- um controle sem caminho;
- um alias ambíguo;
- uma referência desconhecida;
- uma consulta sem intenção explícita de caminho.

O serviço verifica o hash, grava apenas
`artifacts/graph-assisted-retrieval-holdout.local.json` e recusa sobrescrita. O
artefato é local e ignorado pelo Git. Os prechecks anteriores à abertura
passaram com 311 testes, Ruff e mypy em 215 arquivos.

```bash
docker compose run --rm evaluate-graph-assisted-retrieval-holdout
```

## Resultado

- correspondência exata: 8/8;
- cadeias completas pelo gateway: 4/4;
- cadeias completas pelo BM25: 0/4 neste slice adversarial;
- controles corretos: 4/4;
- provenance completa em todas as arestas recuperadas;
- hash observado igual ao hash congelado.

## Limitações

O holdout valida somente perguntas com dois endpoints explícitos sobre um grafo
pequeno, sintético e previamente revisado. O resultado não mede construção do
grafo, extração de relações, atualização temporal, escala, latência, qualidade
de resposta nem desempenho sobre documentos privados.

O desempenho lexical reflete os distratores deste slice e não representa uma
comparação geral entre BM25 e grafos.

## Decisão

O gateway explícito é aprovado como componente estreito, determinístico e
opt-in para grafos revisados. Ele permanece fora do caminho padrão e não
autoriza Graph RAG completo, LLM para entity linking, banco de grafo ou corpus
privado.

O holdout está encerrado e não será reutilizado para tuning. O próximo gate deve
avaliar a admissão e governança de entidades e relações candidatas antes que um
grafo possa ser construído a partir de qualquer processo de extração.

A primeira fronteira dessa admissão foi avaliada no
[Resultado 066](066-graph-catalog-admission-development.md) e atingiu 10/10 em
desenvolvimento sintético.
