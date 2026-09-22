# Resultado 055: gate de admissão de regras estruturadas

## Hipótese

Os achados da auditoria estática podem controlar a entrada do catálogo no motor
de forma fechada: conflitos bloqueiam, redundâncias aguardam revisão explícita e
somente catálogos sem pendências são admitidos.

## Estratégia e dataset

O gate recebe um `RuleSet` e, opcionalmente, pares de versões cuja redundância
foi revisada. A política possui três resultados fechados:

- `rejected` para qualquer conflito;
- `review` para redundância ainda não revisada;
- `admitted` somente quando não resta achado acionável.

Uma referência de revisão ausente dos achados atuais gera erro, evitando que uma
aprovação antiga ou digitada incorretamente seja aceita silenciosamente.
Conflitos têm precedência mesmo quando outra redundância foi revisada.

O dataset público e integralmente sintético
`structured_rule_admission_development.json`, política
`structured-rule-admission-development-v1`, contém cinco casos. Seu SHA-256 é
`d13f485eccf0cd830334df2c5595fcc060e04e0f0fafcda7411ebce580dbf438`.

```bash
docker compose run --rm evaluate-structured-rule-admission
```

## Resultado

- correspondência exata: 100% (5/5);
- catálogo limpo admitido;
- catálogo com conflito rejeitado;
- redundância não revisada encaminhada para revisão;
- redundância revisada admitida;
- conflito permaneceu bloqueante em catálogo que também continha redundância
  revisada;
- 275 testes passaram; Ruff e mypy passaram em 195 arquivos.

## Decisão

O gate está aprovado em desenvolvimento sintético. O próximo passo é congelar
um holdout sintético inédito antes da primeira execução, registrar seu hash e
recusar sobrescrita do relatório local. O conjunto de desenvolvimento não deve
ser confundido com evidência de generalização.

Catálogo privado, extração documental, publicação real e decisões de alto
impacto permanecem bloqueados.

O holdout posterior está registrado no
[Resultado 056](056-structured-rule-admission-holdout.md).
