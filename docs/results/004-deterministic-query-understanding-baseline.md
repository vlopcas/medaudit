# Resultado 004: baseline determinístico de Query Understanding

## Hipótese

Regras lexicais pequenas e interpretáveis conseguem extrair sinais básicos de
roteamento antes do retrieval e oferecem um baseline mensurável para a Fase 8,
sem introduzir outro modelo.

## Configuração

- dataset público com 15 perguntas integralmente sintéticas;
- cinco intenções: auditoria, comparação, consulta documental, consulta externa
  e geral;
- extração de data explícita e código sintético de procedimento;
- sinais booleanos de dados externos e decomposição;
- execução determinística, sem rede, LLM ou acesso ao corpus privado;
- exact match exige acerto simultâneo de todos os cinco campos avaliados.

## Resultado

| Métrica | Resultado |
|---|---:|
| Exact match | 80,0% (12/15) |
| Intenção | 86,7% |
| Data de referência | 100% |
| Código de procedimento | 100% |
| Necessidade de dados externos | 93,3% |
| Necessidade de decomposição | 86,7% |

Três casos falharam. O baseline não reconheceu uma paráfrase de mudança entre
regras como comparação, uma consulta indireta ao valor atual em portal como
dependência externa e o verbo “relacione” como pedido de decomposição.

## Decisão

A hipótese foi aceita como baseline, não como roteador pronto. Os campos
estruturados e as falhas são interpretáveis, mas 80% de exact match ainda não
justifica alterar o caminho do RAG. O próximo experimento deve comparar uma
ampliação controlada das regras ou outra abordagem em novos casos sintéticos,
preservando estes 15 casos como conjunto de desenvolvimento já consultado.

Nenhuma consulta foi reescrita, decomposta ou enviada ao retriever neste marco.

## Reprodução

```bash
docker compose run --rm evaluate-query-understanding
```

