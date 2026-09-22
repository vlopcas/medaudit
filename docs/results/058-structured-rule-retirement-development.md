# Resultado 058: aposentadorias revisadas de regras

## Hipótese

A fronteira de publicação pode aceitar uma remoção legítima sem permitir que
aprovações antigas, parciais ou ambíguas retirem regras silenciosamente.

## Estratégia e dataset

Uma aposentadoria revisada carrega dois vínculos:

- a lista exata de versões removidas, no formato `rule_id@version`;
- o `publication_id` determinístico do snapshot anterior.

A lista deve ser subconjunto das remoções atuais. Se alguma remoção permanecer
sem aprovação, todo o catálogo continua em revisão. Uma referência a snapshot
antigo ou a regra ainda presente é recusada antes da publicação.

O dataset sintético de publicação foi ampliado de nove para onze casos com uma
aposentadoria completa e uma aprovação parcial. A política permanece
`structured-rule-publication-development-v1`. O SHA-256 da versão ampliada é
`878f79cef7eb88c8f811767674df6f8bae86ec22813427932210bd46d6fa375b`.

```bash
docker compose run --rm evaluate-structured-rule-publication
```

## Resultado

- correspondência exata: 100% (11/11);
- aposentadoria completa, vinculada ao snapshot anterior, foi publicada;
- aprovação parcial manteve o catálogo inteiro em revisão;
- testes unitários recusaram snapshot de revisão antigo;
- testes unitários recusaram tentativa de aposentar regra ainda presente;
- 288 testes passaram; Ruff e mypy passaram em 199 arquivos.

## Decisão

O contrato de publicação está completo para o recorte sintético atual e pode
avançar para um holdout inédito, congelado antes da primeira execução. Esse
holdout deve combinar admissão, substituição e aposentadoria sem reutilizar os
casos de desenvolvimento.

Identidade do revisor, assinatura, persistência, controle de acesso, catálogo
privado e publicação real continuam fora do escopo.

O holdout posterior está registrado no
[Resultado 059](059-structured-rule-publication-holdout.md).
