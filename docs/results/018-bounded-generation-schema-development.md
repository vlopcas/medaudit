# Resultado 018: schema limitado da síntese local

## Hipótese e protocolo

Restringir a forma permitida do JSON evitaria a expansão descontrolada que o
limite de tokens apenas truncava. Mantiveram-se modelo, prompt candidato,
dataset, temperatura, limite de 512 tokens e três repetições por caso. A única
nova variável foi o schema `bounded-v1`:

- no máximo quatro claims;
- no máximo 240 caracteres por claim;
- no máximo quatro suportes por claim;
- no máximo quatro citações por suporte.

Foram executadas duas rodadas independentes nos cinco casos integralmente
sintéticos, totalizando 30 tentativas. O dataset permaneceu sob o SHA-256
`cc6e8d5a03a73c1bbf74307e5f6772e4318b67b87cc85c142717d88b99af5795`.

## Resultados

| Métrica | Rodada 1 | Rodada 2 | Combinado |
|---|---:|---:|---:|
| Saída estruturada | 100% (15/15) | 100% (15/15) | 100% (30/30) |
| Contrato grounded | 100% (15/15) | 100% (15/15) | 100% (30/30) |
| Status esperado | 100% (15/15) | 100% (15/15) | 100% (30/30) |
| Conteúdo respondível | 100% (12/12) | 100% (12/12) | 100% (24/24) |
| Recall de conceitos | 100% (33/33) | 100% (33/33) | 100% (66/66) |
| Maior latência | 4,12 s | 4,71 s | 4,71 s |
| Latência média ponta a ponta | 2,03 s | 2,07 s | 2,05 s |

Status e acerto de conteúdo foram estáveis nos cinco casos em ambas as rodadas.
Na primeira, somente a redação estruturada do caso comparativo variou entre
tentativas; todas as variantes continuaram corretas e grounded. A segunda
rodada foi exatamente estável.

Nenhuma tentativa atingiu o limite de 512 tokens ou produziu JSON inválido. O
relatório não persiste prompt, evidência nem texto gerado.

## Decisão

O conjunto `answer-when-supported-v1` + `bounded-v1` + limite de 512 tokens
atingiu o gate de desenvolvimento: 100% de estrutura, provenance e status, além
de conteúdo acima do mínimo de 80%. A configuração fica elegível para um novo
holdout sintético congelado.

Isso não promove a síntese para o runtime e não reabre holdouts anteriores. O
próximo marco deve criar casos inéditos integralmente sintéticos, registrar seu
hash antes da execução e recusar sobrescrita do resultado. Somente esse holdout
poderá decidir se a configuração candidata avança.

## Reprodução

```bash
docker compose run --rm benchmark-local-decomposed-grounding-bounded
```
