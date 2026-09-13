# Resultado 016: política explícita de resposta

## Hipótese e protocolo

Uma única alteração na instrução poderia reduzir a abstention excessiva sem
alterar modelo, dataset, evidências, schema ou temperatura. A variante
`answer-when-supported-v1` acrescenta que o modelo deve responder quando todos
os fatos solicitados estiverem presentes, deve se abster somente quando algum
fato estiver ausente e não pode tratar múltiplos grupos como motivo isolado para
abstention.

Foram mantidos o `Qwen3-4B Q4_K_M`, as três repetições por caso e o dataset
integralmente sintético sob o SHA-256
`cc6e8d5a03a73c1bbf74307e5f6772e4318b67b87cc85c142717d88b99af5795`.
Um teste automatizado confirma que a política modifica somente a instrução;
input, schema e temperatura permanecem iguais ao baseline.

## Resultado instrumentado

| Métrica | Resultado |
|---|---:|
| Saída JSON estruturada | 100% (15/15) |
| Contrato grounded válido | 100% (15/15) |
| Status esperado | 100% (15/15) |
| Conteúdo correto nos casos respondíveis | 100% (12/12) |
| Recall de conceitos obrigatórios | 100% (33/33) |
| Autorização de citações respondidas | 100% |
| Cobertura dos grupos respondidos | 100% |
| Estabilidade exata dentro da rodada | 100% (5/5 casos) |
| Latência média ponta a ponta | 2,06 s |
| Maior latência ponta a ponta | 4,53 s |

A instrumentação mede o tempo de todas as tentativas, inclusive quando o
adaptador não consegue materializar uma resposta. O relatório continua sem
persistir prompt, evidência ou texto gerado.

## Falha de repetibilidade entre rodadas

Uma rodada imediatamente anterior, com a mesma política, modelo, dataset e três
repetições, obteve 14/15 saídas válidas. Uma tentativa gerou até o limite de
contexto de 8.192 tokens, levou aproximadamente 119 segundos e não produziu JSON
utilizável. As demais tentativas daquela rodada atingiram 91,7% de conteúdo
correto nos casos respondíveis.

Assim, a rodada instrumentada perfeita não demonstra repetibilidade operacional
entre execuções independentes. A média de 2,06 segundos também não representa a
cauda observada na rodada anterior; por isso as duas observações são mantidas na
decisão.

## Decisão

A política explícita de resposta é mantida como candidata porque resolveu a
abstention no melhor resultado, mas não é promovida para o contrato principal,
holdout ou runtime. O critério de qualidade foi atingido em uma rodada e violado
na outra.

O próximo experimento deve manter essa política e acrescentar somente um limite
explícito e pequeno de tokens de saída no adaptador local. Depois, novas rodadas
de desenvolvimento deverão demonstrar que a falha longa foi eliminada antes de
consumir um holdout.

## Reprodução

```bash
docker compose run --rm benchmark-local-decomposed-grounding-prompt
```
