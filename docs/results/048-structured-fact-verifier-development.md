# Resultado 048: verificador de fatos estruturados

## Hipótese

Uma estratégia determinística restrita a quantidades com unidade, códigos e
polaridade poderia bloquear contradições que atravessaram a cobertura lexical,
sem assumir que consegue verificar linguagem geral.

## Estratégia e dataset

`StructuredFactVerifier` opera depois da validação estrutural e somente sobre
as evidências citadas por cada claim:

- canonicaliza números simples escritos por extenso e unidades de tempo;
- compara códigos alfanuméricos exatamente;
- canonicaliza polaridade de permissão e proibição;
- encaminha claims sem fatos reconhecidos para revisão;
- encaminha evidência suspeita para revisão;
- libera abstention válida;
- não usa modelo, rede ou conteúdo privado.

O dataset público e integralmente sintético
`structured_fact_verifier_development.json`, política
`structured-fact-verifier-development-v1`, contém dez casos e tem SHA-256
`5061a49ff93d378bc047a714a9ad1e0f17f6de869b801320697f0a30cb98d4b0`.
Ele cobre canonicalização e contradição de quantidade, troca de unidade,
códigos, paráfrase e inversão de polaridade, revisão de linguagem não
estruturada, conteúdo não confiável e abstention.

```bash
docker compose run --rm evaluate-structured-fact-verifier
```

## Resultado

O primeiro ciclo acertou 9/10. A única perda foi uma resposta segura enviada
para revisão porque as flexões `autorizada` e `vedada` ainda não pertenciam ao
vocabulário canônico. A normalização morfológica foi corrigida no conjunto de
desenvolvimento sem adicionar novo tipo de fato.

Após a correção:

- correspondência exata: 100% (10/10);
- casos seguros: 100%;
- casos inseguros: 100%;
- casos destinados a revisão: 100%;
- 263 testes, Ruff e mypy passaram em 181 arquivos.

## Decisão

A candidata está aprovada somente no desenvolvimento e apenas para os três
tipos de fato declarados. Ela pode avançar para um holdout sintético inédito,
congelado antes da primeira execução. Claims fora desse domínio continuam em
revisão, e o componente não deve ser descrito como verificador semântico geral.

O corpus privado e o runtime principal permanecem bloqueados. Nenhum modelo foi
executado neste experimento.
