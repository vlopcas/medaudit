# Resultado 009: holdout do roteamento explícito

## Hipótese e protocolo

Uma política propositalmente estreita consegue proteger o pipeline sem tentar
resolver toda a semântica da pergunta. Ela envia para decomposição somente
comparações lexicais explícitas ou consultas com mais de uma data; dependências
externas explícitas são bloqueadas; os demais casos seguem para retrieval
direto.

O desenvolvimento usou 18 casos e atingiu 100%. Depois foram congelados 15
casos inéditos, cinco por rota, sob o SHA-256
`af76d824e13154270eea06cb7c93c40e570478bacafd5fbce684f0a78513a65a`.
A saída local recusa sobrescrita.

## Resultado do holdout

| Métrica | Resultado |
|---|---:|
| Acurácia geral | 100% (15/15) |
| Retrieval direto | 100% (5/5) |
| Decomposição | 100% (5/5) |
| Dependência externa | 100% (5/5) |

## Decisão

A hipótese foi aceita dentro de seu escopo declarado. O
`ExplicitQueryRouter` foi promovido como política determinística anterior ao
retrieval. O `RoutedEvidenceFirstPipeline` somente chama o pipeline de
evidências para a rota `direct_retrieval`.

Esse resultado não prova compreensão geral de consultas. Formulações implícitas
e ambíguas seguem para retrieval direto por projeto. As rotas de decomposição e
dependência externa encerram sem gerar subconsultas e sem acessar ferramentas.

## Reprodução

O holdout já foi aberto e deve recusar uma segunda execução:

```bash
docker compose run --rm evaluate-explicit-query-routing-holdout
```

