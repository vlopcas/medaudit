# Resultado 012: holdout do agrupamento de evidências

## Hipótese e protocolo

Um agrupador determinístico consegue preservar contexto e citações por passo,
manter repetições contextualmente legítimas e bloquear geração diante de
evidência parcial ou necessidade de esclarecimento.

O desenvolvimento atingiu 100% em seis casos e 11 grupos. Em seguida, a regra
foi congelada e avaliada em quatro casos inéditos e sete grupos sob o SHA-256
`7266046a3475bd142b51f9ee6375c0159e5cd71eba32eadf6ee5a7dcbdde3a63`.

## Resultado do holdout

| Métrica | Resultado |
|---|---:|
| Exact match | 100% (4/4) |
| Preservação de contexto | 100% (7/7) |
| Preservação de citações | 100% (7/7) |
| Gate de geração | 100% (4/4) |

## Decisão

A hipótese foi aceita no contrato sintético avaliado. O agrupador foi integrado
automaticamente quando o pipeline roteado possui um executor configurado. Essa
integração entrega um pacote elegível para futura síntese, mas não chama o LLM.

O próximo ciclo deve definir o contrato de prompt multi-evidência e validar que
uma resposta comparativa cite cada afirmação no grupo correto.

## Reprodução

O holdout já foi aberto e deve recusar uma segunda execução:

```bash
docker compose run --rm evaluate-evidence-aggregation-holdout
```
