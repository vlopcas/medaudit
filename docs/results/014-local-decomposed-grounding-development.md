# Resultado 014: síntese decomposta com LLM local

## Hipótese e protocolo

O `Qwen3-4B Q4_K_M`, executado localmente via `llama.cpp`, deveria preencher o
contrato de claims por passo e responder evidências agrupadas sem perder
provenance. O conjunto de desenvolvimento contém cinco casos integralmente
sintéticos: comparação, transição temporal, cruzamento documental, múltiplas
evidências em um passo e evidência insuficiente.

O experimento isola apenas a síntese. Os pacotes de evidência são construídos
diretamente, sem recuperação, e nenhuma resposta gerada é persistida. O
artefato local registra somente identificadores sintéticos, booleanos, contagens
e latência. O input tem SHA-256
`cc6e8d5a03a73c1bbf74307e5f6772e4318b67b87cc85c142717d88b99af5795`.

## Resultado de desenvolvimento

| Métrica | Resultado |
|---|---:|
| Saída JSON estruturada | 100% (5/5) |
| Contrato grounded válido | 100% (5/5) |
| Status esperado | 40% (2/5) |
| Conteúdo correto nos casos respondíveis | 25% (1/4) |
| Recall de conceitos obrigatórios | 18,2% (2/11) |
| Autorização de citações respondidas | 100% |
| Cobertura dos grupos respondidos | 100% |
| Latência média | 765 ms |

O modelo respondeu corretamente o caso de cruzamento documental e se absteve
corretamente no caso sem evidência. Nos outros três casos respondíveis, recusou
responder. A única resposta `answered` usou citações autorizadas e cobriu ambos
os grupos, mas isso representa somente uma observação.

Uma execução diagnóstica imediatamente anterior havia produzido abstention nos
cinco casos. Essa variação, apesar da temperatura zero, mostra que uma execução
isolada não basta para caracterizar estabilidade do backend local.

## Decisão

A hipótese foi rejeitada no desenvolvimento. O modelo e prompt atuais não
seguem para holdout e a síntese decomposta permanece fora do runtime. O
validador fez seu papel ao aceitar abstentions bem formadas, mas conformidade de
schema não demonstra utilidade de resposta.

O próximo ciclo deve medir repetibilidade, diagnosticar por que o prompt
conservador induz abstention excessiva e testar uma alteração única no conjunto
de desenvolvimento. O holdout só será criado depois de uma política de
promoção explícita ser
atingida: 100% de estrutura e provenance, 100% de status e pelo menos 80% de
conteúdo correto nos casos respondíveis.

## Reprodução

```bash
docker compose run --rm benchmark-local-decomposed-grounding
```
