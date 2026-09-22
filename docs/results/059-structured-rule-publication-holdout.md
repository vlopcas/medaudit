# Resultado 059: holdout da publicação de regras

## Hipótese

A fronteira completa de publicação preservaria admissão, versionamento,
substituição e aposentadoria em casos sintéticos inéditos, sem ajuste após a
abertura do conjunto.

## Congelamento

O dataset `structured_rule_publication_holdout.json`, política
`structured-rule-publication-holdout-v1`, contém oito casos integralmente
sintéticos. Ele foi congelado no commit `aa24623` antes da primeira execução.
Seu SHA-256 é
`25b1ef2c399e421db79dcad91baf1eab9449dd24c010fb158dfeea915899b824`.

Os prechecks passaram com 289 testes, Ruff e mypy em 199 arquivos. O conjunto de
desenvolvimento permaneceu em 11/11. O serviço verifica o hash, grava um relatório
`.local.json` ignorado pelo Git e usa `--refuse-overwrite`.

```bash
docker compose run --rm evaluate-structured-rule-publication-holdout
```

## Resultado

- correspondência exata: 100% (8/8);
- snapshot inicial foi publicado em ordem determinística;
- conflito de admissão bloqueou uma atualização;
- redundância e substituição revisadas em conjunto foram publicadas;
- substituição não revisada permaneceu em revisão;
- aposentadoria revisada junto de uma adição foi publicada;
- aposentadoria parcial permaneceu em revisão;
- mutação da origem sob a mesma versão foi bloqueada;
- regressão de versão foi bloqueada;
- o hash observado correspondeu ao congelado;
- uma segunda chamada foi recusada antes da avaliação porque o relatório já
  existia.

## Decisão

A fronteira de publicação está aprovada somente para o contrato sintético
avaliado. O holdout está encerrado e não será usado para tuning. O próximo passo
é executar o checkpoint arquitetural da Fase 9 e decidir se regras estruturadas
já atendem o problema formalizado ou se existe uma necessidade mensurável de
grafo.

Identidade do revisor, assinatura, persistência, controle de acesso, catálogo
privado e publicação real permanecem bloqueados.
