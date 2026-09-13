# Resultado 010: holdout do planejamento determinístico

## Hipótese e protocolo

Consultas já roteadas para decomposição podem receber um plano seguro sem
recorrer a um LLM: múltiplas datas geram snapshots independentes; comparações
com dois lados sintaticamente separáveis geram dois escopos; as demais pedem
esclarecimento.

O desenvolvimento usou 12 casos sintéticos e atingiu 100% de exact match. As
regras foram então congeladas e avaliadas uma única vez em 12 casos inéditos,
sob o SHA-256
`1393d8387c7460de8210b9cfb584f22bd5560484a9eab264ea17fd2665a69303`.

## Resultado do holdout

| Métrica | Resultado |
|---|---:|
| Exact match geral | 100% (12/12) |
| Planos prontos | 100% (7/7) |
| Necessidade de esclarecimento | 100% (5/5) |

O exact match exige correspondência simultânea de status, estratégia,
quantidade de passos, datas de referência e escopos.

## Decisão

A hipótese foi aceita dentro do vocabulário sintático avaliado. O planejador
foi integrado à decisão roteada, porém seus passos não são executados. Esse
limite evita confundir planejamento correto com recuperação ou síntese
comparativa corretas, que ainda não foram medidas.

## Reprodução

O holdout já foi aberto e deve recusar uma segunda execução:

```bash
docker compose run --rm evaluate-query-planning-holdout
```
