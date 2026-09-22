# Resultado 054: auditoria estática de regras estruturadas

## Hipótese

Um catálogo de regras revisadas pode ser inspecionado antes da execução para
identificar sobreposições acionáveis de mesma prioridade, sem confundir regras
separadas por escopo, vigência ou condições incompatíveis.

## Estratégia e dataset

O auditor compara cada par de regras e exige simultaneamente:

- mesmo sujeito, ação e prioridade;
- interseção dos períodos de vigência, com limites inclusivos;
- condições compatíveis, isto é, nenhum atributo compartilhado com valores
  diferentes.

Se o par puder corresponder à mesma consulta, decisões divergentes produzem
`conflicting_overlap` e decisões iguais produzem `redundant_overlap`. Os IDs e
versões são ordenados para tornar o relatório determinístico.

O dataset público e integralmente sintético
`structured_rule_audit_development.json`, política
`structured-rule-audit-development-v1`, contém nove regras. Seu SHA-256 é
`26dd74b02f9053ac06366ad280ee7b7a3b7fcfd88baf65b46758491684d0f16c`.

```bash
docker compose run --rm evaluate-structured-rule-audit
```

## Resultado

- correspondência exata com os achados esperados: 100%;
- três achados: dois conflitos e uma redundância;
- condições em chaves distintas foram corretamente tratadas como compatíveis,
  pois podem coexistir numa mesma consulta;
- valores incompatíveis, prioridade diferente, períodos apenas adjacentes e
  escopos distintos não produziram alertas;
- 270 testes passaram; Ruff e mypy passaram em 191 arquivos.

## Decisão

A auditoria está aprovada como componente de desenvolvimento sintético. Ela
detecta problemas, mas ainda não controla a publicação do catálogo. O próximo
gate deve implementar uma fronteira de admissão que bloqueie conflitos e exija
revisão explícita das redundâncias. Somente depois dessa política passar em
novos casos de desenvolvimento será considerado um holdout inédito e congelado.

Esse gate foi implementado e validado posteriormente no
[Resultado 055](055-structured-rule-admission-development.md).

Catálogo privado, extração documental automática e decisões reais permanecem
fora do escopo.
