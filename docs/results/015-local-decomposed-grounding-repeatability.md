# Resultado 015: repetibilidade da síntese decomposta

## Hipótese e protocolo

A variação observada no primeiro benchmark poderia ser localizada e medida sem
alterar prompt, modelo ou dataset. Foram executadas três repetições de cada um
dos cinco casos integralmente sintéticos do Resultado 014, totalizando 15
gerações com o `Qwen3-4B Q4_K_M` via `llama.cpp`.

O benchmark calcula hashes das respostas estruturadas apenas em memória. O
relatório não persiste texto gerado, prompt nem evidência: contém somente IDs
sintéticos, contagens, booleanos, taxas e latência. O dataset permaneceu sob o
SHA-256
`cc6e8d5a03a73c1bbf74307e5f6772e4318b67b87cc85c142717d88b99af5795`.

## Resultado

| Métrica | Resultado |
|---|---:|
| Saída JSON estruturada | 100% (15/15) |
| Contrato grounded válido | 100% (15/15) |
| Status esperado | 33,3% (5/15) |
| Conteúdo correto nos casos respondíveis | 16,7% (2/12) |
| Recall de conceitos obrigatórios | 12,1% (4/33) |
| Resposta estruturada exatamente estável | 80% (4/5 casos) |
| Status estável | 80% (4/5 casos) |
| Acerto de conteúdo estável | 80% (4/5 casos) |
| Latência média | 671 ms |

Comparação, transição temporal e múltiplas evidências no mesmo passo produziram
abstention nas três tentativas. O caso sem evidência também foi estável e
correto. O caso de cruzamento documental foi respondido corretamente em duas
tentativas e recebeu abstention em uma; foi o único caso com variação exata, de
status e de acerto de conteúdo.

As taxas de estabilidade de 80% não indicam boa qualidade: três dos quatro
casos respondíveis foram estáveis no comportamento errado. Elas apenas isolam a
variabilidade de execução da abstention excessiva.

## Decisão

O modelo e prompt atuais continuam rejeitados e não avançam para holdout ou
runtime. O diagnóstico mostra dois problemas separados:

1. abstention sistemática em três formatos de pergunta respondível;
2. instabilidade no único formato em que o modelo conseguiu responder.

O próximo experimento deve alterar somente a instrução de decisão entre
`answered` e `insufficient_evidence`, mantendo modelo, schema, dataset e três
repetições. A promoção continua exigindo 100% de estrutura e provenance, 100%
de status e pelo menos 80% de conteúdo correto.

## Reprodução

```bash
docker compose run --rm benchmark-local-decomposed-grounding
```
