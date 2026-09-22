# Resultado 057: fronteira de publicação de regras

## Hipótese

Uma fronteira determinística pode publicar somente catálogos admitidos,
preservar provenance por versão e impedir alterações silenciosas entre
snapshots.

## Estratégia e dataset

`publish_rule_set` recalcula a admissão e só produz um `PublishedRuleCatalog`
quando não há pendências. O snapshot ordena as regras e recebe uma identidade
SHA-256 derivada de todo o conteúdo estruturado. Ao comparar com uma publicação
anterior, a fronteira:

- bloqueia mudança de conteúdo sob o mesmo `rule_id@version`;
- bloqueia introdução de versão menor ou igual à maior versão anterior;
- exige revisão explícita do par anterior/novo para uma substituição;
- recusa referências de revisão que não correspondem às mudanças atuais;
- encaminha remoções silenciosas para revisão.

O dataset público e integralmente sintético
`structured_rule_publication_development.json`, política
`structured-rule-publication-development-v1`, contém nove casos. Seu SHA-256 é
`9e0166e0cd907ea7eac4ecb5b09aa1d2cfc7c25ef5203279f40781df3a045832`.
Esse snapshot histórico está no commit `61e96b4`; o dataset de desenvolvimento
foi ampliado posteriormente, sem alterar este resultado, no
[Resultado 058](058-structured-rule-retirement-development.md).

```bash
docker compose run --rm evaluate-structured-rule-publication
```

## Resultado

- correspondência exata: 100% (9/9);
- publicação inicial preservou versões e ordenou o snapshot;
- conflito e redundância pendente não produziram catálogo;
- redundância revisada foi publicada;
- reescrita da mesma versão e versão não monotônica foram bloqueadas;
- substituição sem revisão e remoção silenciosa ficaram em revisão;
- substituição explicitamente revisada foi publicada;
- 284 testes passaram; Ruff e mypy passaram em 199 arquivos.

## Decisão

A fronteira está aprovada somente em desenvolvimento sintético. Ela ainda não
avança para holdout porque uma remoção legítima não possui caminho de aprovação.
O próximo incremento deve introduzir aposentadorias explicitamente revisadas,
recusar referências desatualizadas e manter a identidade determinística do
snapshot.

Persistência, assinatura, controle de acesso, catálogo privado e publicação real
permanecem bloqueados.
