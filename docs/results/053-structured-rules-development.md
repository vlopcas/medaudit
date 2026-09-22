# Resultado 053: baseline de regras estruturadas

## Hipótese

Regras revisadas com schema versionado poderiam ser resolvidas por data,
condições e prioridade de modo determinístico, preservando conflitos e ausência
de regra como estados explícitos.

## Estratégia e dataset

O módulo `medaudit.rules` introduz:

- `StructuredRule` e `RuleSet` versionados;
- decisões fechadas `allow` e `deny`;
- vigência inclusiva, prioridade e condições exatas;
- provenance por `rule_id@version`;
- resultados `applied`, `no_match` e `review` com códigos fechados;
- invariantes que recusam períodos inválidos, condições duplicadas, versões
  duplicadas e combinações impossíveis de status e código.

O dataset público e integralmente sintético `structured_rules_development.json`,
política `structured-rules-development-v1`, contém seis regras e oito casos. Seu
SHA-256 é
`8cf108671efa7a249530b18a8f3af771504262933270198807fe06625f2fd21d`.

```bash
docker compose run --rm evaluate-structured-rules
```

## Resultado

- correspondência exata: 100% (8/8);
- regra específica e fallback geral foram selecionados corretamente;
- exceção de maior prioridade prevaleceu;
- transição temporal e último dia inclusivo foram respeitados;
- conflito na mesma prioridade foi encaminhado para revisão;
- condição ausente e escopo desconhecido produziram `no_match`;
- 269 testes, Ruff e mypy passaram em 188 arquivos.

## Decisão

O baseline está aprovado somente em desenvolvimento sintético. Ele não recebe
texto documental bruto nem usa LLM. O próximo gate deve ampliar a validação do
catálogo de regras — incluindo auditoria estática de sobreposição e conflitos —
antes de congelar um holdout inédito do motor.

Integração com o catálogo privado, extração automática e decisões de alto
impacto permanecem bloqueadas.
