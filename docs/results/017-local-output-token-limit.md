# Resultado 017: limite de saída da síntese local

## Hipótese e protocolo

Um limite explícito de 512 tokens no adaptador local deveria eliminar a cauda de
aproximadamente 119 segundos observada com a política
`answer-when-supported-v1`, sem mudar prompt, modelo, dataset, schema,
temperatura ou número de repetições.

O `LlamaCppClient` passou a aceitar um limite opcional, validá-lo e enviá-lo ao
`llama.cpp` como `max_tokens`. Foram executadas duas rodadas independentes de
três repetições nos cinco casos integralmente sintéticos, totalizando 30
tentativas. O dataset permaneceu sob o SHA-256
`cc6e8d5a03a73c1bbf74307e5f6772e4318b67b87cc85c142717d88b99af5795`.

## Resultados

| Métrica | Rodada 1 | Rodada 2 | Combinado |
|---|---:|---:|---:|
| Saída estruturada | 93,3% (14/15) | 100% (15/15) | 96,7% (29/30) |
| Contrato grounded | 93,3% (14/15) | 100% (15/15) | 96,7% (29/30) |
| Status esperado | 93,3% (14/15) | 100% (15/15) | 96,7% (29/30) |
| Conteúdo respondível | 91,7% (11/12) | 100% (12/12) | 95,8% (23/24) |
| Maior latência | 6,88 s | 4,76 s | 6,88 s |
| Latência média ponta a ponta | 2,37 s | 2,08 s | 2,23 s |

Na primeira rodada, uma das três tentativas do caso de comparação atingiu o
limite de 512 tokens e terminou sem JSON utilizável. A segunda rodada foi
perfeita. A falha ficou limitada a menos de sete segundos, em contraste com os
aproximadamente 119 segundos sem limite, mas não desapareceu.

O relatório mede latência ponta a ponta inclusive nas tentativas inválidas e
continua sem persistir prompts, evidências ou textos gerados.

## Decisão

O limite de 512 tokens é mantido como proteção operacional no experimento, mas
o candidato não avança para holdout ou runtime. Truncar cedo reduz custo e
latência, porém ainda permite resposta inválida e não atende ao gate de 100% de
estrutura, provenance e status.

O próximo experimento deve manter o limite e restringir a própria estrutura do
schema — quantidade de claims, suportes, citações e tamanho do texto — para que
a gramática não permita expansão descontrolada. Seus resultados estão no
[Resultado 018](018-bounded-generation-schema-development.md).

## Reprodução

```bash
docker compose run --rm benchmark-local-decomposed-grounding-capped
```
