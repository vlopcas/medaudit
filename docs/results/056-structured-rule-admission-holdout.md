# Resultado 056: holdout do gate de admissão de regras

## Hipótese

O gate aprovado em desenvolvimento preservaria sua política de falha fechada em
casos sintéticos inéditos, sem ajuste após a abertura do conjunto.

## Congelamento

O dataset `structured_rule_admission_holdout.json`, política
`structured-rule-admission-holdout-v1`, contém seis casos integralmente
sintéticos. Ele foi congelado no commit `513ae33` antes da primeira execução.
Seu SHA-256 é
`64291089e2e103a158fae915896c6605c6cd0cde5acd6bb1541d88e016b57490`.

Os prechecks anteriores à abertura passaram com 276 testes, Ruff e mypy em 195
arquivos. O conjunto de desenvolvimento permaneceu em 5/5. O serviço valida o
hash, grava somente um relatório `.local.json` ignorado pelo Git e usa
`--refuse-overwrite`.

```bash
docker compose run --rm evaluate-structured-rule-admission-holdout
```

## Resultado

- correspondência exata: 100% (6/6);
- separação temporal e atributos incompatíveis foram admitidos sem falso
  conflito;
- conflito entre condições em chaves diferentes foi bloqueado;
- duas redundâncias pendentes foram encaminhadas para revisão;
- as mesmas duas redundâncias, quando explicitamente revisadas, foram admitidas;
- conflito prevaleceu sobre uma redundância ainda pendente;
- o hash observado correspondeu ao valor congelado;
- uma segunda chamada foi recusada antes da avaliação porque o relatório já
  existia.

## Decisão

O gate de admissão está aprovado somente para o contrato sintético avaliado. O
holdout está encerrado e não será usado para tuning. O próximo ciclo deve criar
novos casos de desenvolvimento para uma fronteira de publicação que preserve
provenance por identidade e versão.

Essa aprovação não autoriza extração automática, catálogo privado, publicação
real nem decisões de alto impacto.

A primeira fronteira de publicação posterior está registrada no
[Resultado 057](057-structured-rule-publication-development.md).
