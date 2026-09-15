# Resultado 027: holdout do renderer de contexto compilado

## Hipótese e protocolo

O renderer aprovado no desenvolvimento adversarial deveria recusar mutações
estruturais inéditas e alterações posteriores à compilação. O holdout foi
congelado antes da execução no commit `966da90`, com SHA-256
`babe42a32fb9b82d88ce7766f4c8d602ea6dba4837c8360338a98b28b022120f`.

O conjunto integralmente sintético contém um controle válido e sete mutações:
ID repetido dentro de um grupo, membership de passo ausente ou adicional,
alteração de evidência, instrução ou consulta após compilação e inversão da ordem
dos grupos. O relatório exige o hash congelado e recusa sobrescrita.

## Resultados

| Métrica | Resultado |
|---|---:|
| Correspondência exata | 25% (2/8) |
| Rejeição de mutações inseguras | 28,57% (2/7) |
| Controle válido | 100% (1/1) |
| Integridade de conteúdo | 0% (0/3) |
| Cardinalidade de grupo | 0% (0/1) |
| Ordem de grupos | 0% (0/1) |
| Membership de provenance | 50% (1/2) |

O renderer recusou membership vazio. A duplicata de evidência também foi
recusada, mas por deixar outra evidência sem referência, e não pela invariável
de unicidade esperada; por isso o caso não teve correspondência exata. Foram
aceitas indevidamente alterações posteriores em instrução, consulta e texto de
evidência, um membership adicional de passo e a inversão dos grupos.

## Decisão

O renderer foi rejeitado para ativação no runtime. Objetos imutáveis em Python
podem ser reconstruídos com `replace`, portanto `frozen=True` não comprova que o
conteúdo renderizado é aquele originalmente compilado. Validar somente status,
contagem e confiança não cobre integridade nem toda a topologia.

Este holdout permanece congelado e não será usado para acrescentar condições ao
renderer atual. Uma nova candidata de desenvolvimento deve selar uma
representação canônica do contexto com digest, revalidá-la imediatamente antes
da renderização e representar explicitamente ordem, cardinalidade e memberships
permitidos. Depois exigirá outro holdout inédito.

## Reprodução

A primeira execução já materializou o relatório local. Reexecutar deve falhar
em vez de sobrescrevê-lo:

```bash
docker compose run --rm evaluate-compiled-context-security-holdout
```
