# Resultado 013: holdout da validação grounded decomposta

## Hipótese e protocolo

O contrato determinístico consegue aceitar respostas estruturadas válidas e
rejeitar violações de provenance, cobertura e abstention antes de qualquer uso
de modelo real.

O desenvolvimento atingiu 100% em 12 categorias. Depois do congelamento, o
holdout exercitou oito ramos inéditos sob o SHA-256
`96fdb58b2d3ad989dd77c930414103b69988dfee4ee5eb99fad8dc065db80353`.

## Resultado do holdout

| Métrica | Resultado |
|---|---:|
| Exact match geral | 100% (8/8) |
| Categorias com 100% | 8/8 |

O holdout incluiu resposta e abstention válidas, tipos incorretos, claim não
estruturada, texto vazio, suporte inválido, citações vazias e omissão de grupo.

## Decisão

A hipótese foi aceita. O request e o validador foram promovidos como contrato
provider-neutral para uma futura síntese decomposta. Nenhum cliente LLM foi
conectado neste experimento; qualidade de conteúdo continua não demonstrada.

## Reprodução

O holdout já foi aberto e deve recusar uma segunda execução:

```bash
docker compose run --rm evaluate-decomposed-grounding-holdout
```
