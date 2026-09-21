# Resultado 049: holdout do verificador de fatos estruturados

## Objetivo

Avaliar uma única vez, em casos sintéticos inéditos e previamente congelados,
se o `StructuredFactVerifier` preserva respostas seguras e bloqueia
contradições dentro de seu domínio estreito.

## Congelamento e execução

O dataset `structured_fact_verifier_holdout.json`, política
`structured-fact-verifier-holdout-v1`, foi congelado no commit `9ce28aa` antes
da primeira execução. Seu SHA-256 é
`b4e5146886ed4b270939679925d977efcdf533e4aad1c8f636e4ec0032b15087`.

O runner confere esse hash e recusa sobrescrever o relatório local:

```bash
docker compose run --rm evaluate-structured-fact-verifier-holdout
```

O artefato `artifacts/structured-fact-verifier-holdout.local.json` é privado ao
ambiente de desenvolvimento, ignorado pelo Git e não contém o corpus real.

## Resultado

- correspondência exata: 100% (10/10);
- casos seguros: 100%;
- casos inseguros: 100%;
- casos destinados a revisão: 100%;
- quantidade, unidade, código, polaridade e combinação de fatos tiveram as
  decisões esperadas;
- linguagem fora do domínio permaneceu em revisão;
- abstention segura foi liberada;
- nenhum modelo, rede ou documento privado participou da avaliação.

## Decisão

O verificador estruturado está aprovado como componente experimental opt-in
somente para quantidades com unidade, códigos alfanuméricos e polaridade de
permissão ou proibição. O holdout está encerrado e não será usado para ajuste.

Claims fora desses tipos continuam em revisão. A aprovação não transforma o
componente em verificador semântico geral, não promove automaticamente a
síntese local reprovada e não libera o corpus privado nem o runtime principal.
