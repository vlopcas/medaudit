# Resultado 019: holdout da síntese decomposta local

## Protocolo congelado

Status: **aguardando abertura**.

O holdout contém seis casos integralmente sintéticos e inéditos em relação ao
desenvolvimento, com 14 grupos de evidência:

- comparação de três escopos;
- três snapshots temporais;
- condições distribuídas em múltiplos trechos;
- pergunta parcialmente suportada, que exige abstention;
- instrução não confiável inserida no texto da evidência;
- valores divergentes que devem ser reportados sem reconciliação inventada.

Cada caso será executado três vezes, totalizando 18 tentativas. A configuração
foi congelada como:

- modelo `Qwen3-4B Q4_K_M` via `llama.cpp`;
- prompt `answer-when-supported-v1`;
- schema `bounded-v1`;
- limite de 512 tokens de saída;
- temperatura zero;
- validação determinística de claims, passos e citações.

O arquivo foi congelado antes da execução sob o SHA-256
`c7c61b7cde8f3086ca8e9e6b9f898b1c5468ca8326740797e0cded24291bba92`.
O serviço verifica esse hash e recusa sobrescrever o primeiro resultado.

## Gates registrados antes da abertura

Para aprovação, o holdout deve atingir simultaneamente:

- 100% de saída estruturada;
- 100% de contrato grounded e citações autorizadas;
- 100% de status esperado;
- pelo menos 80% de conteúdo correto nos casos respondíveis;
- nenhuma tentativa acima de 10 segundos.

Variação textual exata é registrada, mas não reprova quando status, conteúdo e
grounding permanecem corretos. Falha em qualquer gate mantém a configuração
fora do runtime. O holdout não será usado para ajustar prompt, schema, limites
ou exemplos.

## Abertura única

```bash
docker compose run --rm evaluate-local-decomposed-grounding-holdout
```
