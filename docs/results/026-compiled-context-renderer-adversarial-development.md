# Resultado 026: renderer de contexto em desenvolvimento adversarial

## Hipótese e protocolo

O renderer de `CompiledContext` deve aceitar apenas um contexto íntegro e
recusar adulterações de status, budget, identidade, confiança ou provenance
antes de produzir um `LLMRequest`. O protocolo
`compiled-context-renderer-adversarial-v1` parte de um contexto integralmente
sintético válido e aplica uma mutação isolada por caso.

O dataset tem SHA-256
`f3a695eecf9a8c8afb3e218a52db8191c1201d5d4378eb588f3fed19ce04be9a`.
Ele contém um controle válido e doze mutações distribuídas por seis categorias.
O relatório registra somente IDs, categorias, mutações e decisões, sem texto de
consulta ou evidência.

## Resultados

| Métrica | Resultado |
|---|---:|
| Correspondência exata | 100% (13/13) |
| Rejeição de mutações inseguras | 100% (12/12) |
| Categorias com 100% | 6/6 |

Foram recusados status não pronto, estouro e inconsistência de budget, IDs de
item ou grupo duplicados, instrução sem confiança de controle, consulta ou
evidência elevadas a controle, referência ausente, vínculo com passo incorreto,
evidência não referenciada e grupo vazio. O controle íntegro foi renderizado.

## Decisão

A fronteira está aprovada somente no desenvolvimento adversarial. O próximo
passo é congelar um holdout estrutural inédito, com combinações que não repitam
as mutações usadas aqui. O renderer e o compilador continuam opt-in; nenhum
modelo foi chamado e o runtime privado permanece inalterado.

## Reprodução

```bash
docker compose run --rm evaluate-compiled-context-security
```
