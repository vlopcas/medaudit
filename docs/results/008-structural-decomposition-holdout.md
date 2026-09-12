# Resultado 008: decomposição estrutural de consultas

## Hipótese e protocolo

Sinais de estrutura textual poderiam reconhecer consultas multi-documento sem
uma lista crescente de verbos. A candidata detecta escopo explícito, fontes
repetidas coordenadas, pares rotulados e partes solicitadas separadamente.

O desenvolvimento usou 20 perguntas sintéticas balanceadas e atingiu 100%. Em
seguida, foram congelados 16 casos novos, também balanceados, incluindo usos
adversariais das mesmas construções. O SHA-256 do holdout é
`b25cdca3d1462af091953ce1c1552e1d7819347029c34d67fea4e5c3b04dc06c` e o
relatório local recusa sobrescrita.

## Resultado do holdout

| Métrica | Resultado |
|---|---:|
| Acurácia | 62,5% |
| Precisão | 62,5% |
| Recall | 62,5% |
| Taxa de falsos positivos | 37,5% |
| Verdadeiros positivos | 5/8 |
| Verdadeiros negativos | 5/8 |

Houve três falsos negativos e três falsos positivos. Expressões como “ambos”
e “respectivamente” fora de uma solicitação multi-documento acionaram a regra,
enquanto algumas variações legítimas de “cada” e “os dois” não foram cobertas.

## Decisão

A hipótese foi rejeitada. A heurística não integra o analisador nem o roteador
principal e o holdout não será usado para ampliar seus padrões. Código, dataset
e avaliador permanecem como registro reproduzível do experimento.

Esse resultado reforça que detectar a necessidade de decomposição apenas pela
superfície da pergunta é frágil. O próximo marco deve reduzir o escopo: gerar
planos somente quando o usuário pedir explicitamente comparação ou múltiplas
datas, mantendo os demais casos em retrieval direto até existir evidência
melhor.

## Reprodução

O holdout já foi aberto e deve recusar uma segunda execução:

```bash
docker compose run --rm evaluate-structural-decomposition-holdout
```

