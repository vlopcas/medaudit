# Resultado 029: holdout do renderer de contexto selado

## Hipótese e protocolo

A candidata aprovada no desenvolvimento deveria detectar transformações
inéditas e compostas no contexto compilado. O dataset integralmente sintético
foi congelado antes da primeira execução no commit `ae10d0e`, com SHA-256
`f59a80abe57cd802c5f1656dc9c998399daf4bfb66d5bdc14b74e5c9e8aaf412`.
O renderer não foi alterado depois do congelamento.

O relatório local foi materializado uma única vez pelo serviço com rede
desabilitada e proteção contra sobrescrita:

```bash
docker compose run --rm evaluate-sealed-context-security-holdout
```

## Resultado observado

| Métrica bruta | Resultado |
|---|---:|
| Correspondência exata | 76,92% (10/13) |
| Rejeição rotulada como insegura | 75% (9/12) |
| Controle válido | 100% (1/1) |
| Mutações que efetivamente alteraram o contexto | 100% (9/9 recusadas) |

As três divergências não foram falhas do selo. O adaptador compartilhado
`build_bundle` materializa `page` e `section` como `None`, independentemente dos
valores declarados no JSON. Além disso, grupos temporais usam `scope=None` por
contrato. Portanto, limpar página, limpar seção e trocar os dois escopos já
nulos produziu objetos exatamente iguais ao controle. O digest permaneceu
válido porque não houve alteração representada.

## Decisão

O holdout é **inconclusivo por defeito do harness**. Não se recalculam suas
métricas, não se alteram casos congelados e não se promove a candidata. Embora
todas as nove mutações efetivas tenham sido recusadas, o conjunto não executou
três desafios que afirmava executar.

Antes de outro holdout, o avaliador deve falhar explicitamente quando uma
mutação gerar um contexto igual ao original e deve construir provenance e
metadados compatíveis com os campos que pretende desafiar. Depois disso será
necessário congelar um dataset novo. Renderer, runtime, modelo e corpus privado
continuam inalterados.

## Remediação posterior

Sem reexecutar ou alterar este holdout, o harness passou a abortar quando uma
mutação não modifica o `CompiledContext`. O adaptador sintético também passou a
preservar `page` e `section` opcionais. Dois testes automatizados cobrem essas
pré-condições. Essa correção valida o instrumento futuro; não muda as métricas
nem a decisão desta execução.
