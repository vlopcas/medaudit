# Resultado 005: holdout sintético de Query Understanding

## Hipótese e protocolo

Uma ampliação limitada às três falhas do Resultado 004 deveria generalizar para
novas formulações sintéticas. Antes da execução foram congelados:

- 12 casos inéditos para este ciclo;
- as mesmas cinco intenções e os mesmos cinco campos avaliados;
- casos com paráfrases de comparação, consulta externa e decomposição;
- SHA-256 `3dd6b687ff255e36414b33a4e7ecfe0e35ce6aa1b70af96b92da92f65f4e8364`;
- caminho de saída local que recusa sobrescrita.

As regras foram alteradas somente a partir dos três erros do conjunto de
desenvolvimento. Esse conjunto passou de 80% para 100% de exact match antes da
abertura do holdout.

## Resultado

| Métrica | Resultado |
|---|---:|
| Exact match | 66,7% (8/12) |
| Intenção | 83,3% |
| Data de referência | 100% |
| Código de procedimento | 100% |
| Necessidade de dados externos | 100% |
| Necessidade de decomposição | 66,7% |

Quatro casos falharam. Duas paráfrases de comparação não foram classificadas
nem marcadas para decomposição. Duas formulações multi-documento adicionais
tiveram a intenção documental reconhecida, mas não acionaram decomposição.

## Decisão

A hipótese de generalização foi rejeitada. O baseline continua útil para
normalização, datas, códigos explícitos e bloqueio de dependências externas,
mas suas decisões de intenção e decomposição não devem controlar o RAG.

O holdout não será usado para adicionar novos termos às regras. O próximo ciclo
deve formular outra abordagem e usar novos dados de desenvolvimento, mantendo
este resultado como avaliação final imutável da variante determinística v1.

## Reprodução

O comando abaixo já foi executado e agora deve recusar a sobrescrita do
relatório local:

```bash
docker compose run --rm evaluate-query-understanding-holdout
```

