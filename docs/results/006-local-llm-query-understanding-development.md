# Resultado 006: Query Understanding híbrido com LLM local

## Hipótese

Manter datas e códigos sob extração determinística e delegar somente intenção,
dependência externa e decomposição ao modelo local deveria superar a fragilidade
lexical do baseline sem entregar ao modelo responsabilidades factuais.

## Configuração

- 16 perguntas novas e integralmente sintéticas para desenvolvimento;
- extração determinística de datas e códigos de oito dígitos;
- `Qwen3-4B Q4_K_M` via `llama.cpp` local para três campos semânticos;
- temperatura zero e saída restringida por JSON Schema;
- nenhuma montagem do corpus privado e nenhuma API externa;
- relatório local contendo somente métricas, IDs e campos incorretos.

## Resultado

| Métrica | Resultado |
|---|---:|
| Exact match | 56,25% (9/16) |
| Intenção | 75,0% |
| Data de referência | 100% |
| Código de procedimento | 100% |
| Necessidade de dados externos | 75,0% |
| Necessidade de decomposição | 87,5% |
| Latência média do modelo | 348 ms |

Sete casos falharam em pelo menos um campo. O modelo marcou dependência externa
indevida em perguntas respondíveis por documentos, confundiu intenções de
auditoria e consulta documental e ainda perdeu duas necessidades de
decomposição.

## Decisão

A hipótese foi rejeitada ainda no desenvolvimento. O resultado é inferior aos
80% iniciais do baseline determinístico e acrescenta custo, latência e uma nova
falha possível. Nenhum holdout será consumido para esta variante e ela não será
integrada ao RAG.

O contrato e o benchmark permanecem no projeto como material de estudo. Uma
próxima abordagem deve separar detecção conservadora de bloqueios e planejamento
de consultas, em vez de exigir que uma única classificação resolva ambos.

## Reprodução

```bash
docker compose run --rm benchmark-local-query-understanding
docker compose stop llm-server
```

