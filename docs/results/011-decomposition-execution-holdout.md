# Resultado 011: holdout da execução de decomposição

## Hipótese e protocolo

Um executor determinístico consegue preservar isolamento entre escopos e
snapshots, recuperar o documento esperado em cada passo e se abster no agregado
quando qualquer evidência faltar.

O desenvolvimento usou 12 casos sintéticos e atingiu 100% nas três métricas.
Em seguida, código e parâmetros foram congelados com BM25, `top_k=1` e limiar
`0.1`. O holdout usou corpus, datas e vocabulário inéditos sob o SHA-256
`db4effc3b23a28cebb6d9cea6137a5b2589a9674e902279ee155c811a22395c9`.

## Resultado do holdout

| Métrica | Resultado |
|---|---:|
| Exact match dos casos | 100% (10/10) |
| Documento correto por passo | 100% (17/17) |
| Documento correto por passo temporal | 100% (9/9) |

O exact match exige simultaneamente o status agregado e a sequência completa de
documentos esperados, incluindo passos que devem se abster.

## Decisão

A hipótese foi aceita no escopo sintético avaliado. O executor foi promovido
como dependência opcional do pipeline roteado. Ele não é criado implicitamente:
consultas temporais só podem ser executadas quando o chamador fornecer um
resolvedor de snapshots por data.

O resultado não valida combinação de evidências nem qualidade de resposta
comparativa. Essas responsabilidades continuam bloqueadas para o próximo ciclo.

## Reprodução

O holdout já foi aberto e deve recusar uma segunda execução:

```bash
docker compose run --rm benchmark-decomposition-execution-holdout
```
