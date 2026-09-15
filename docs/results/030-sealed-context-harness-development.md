# Resultado 030: harness de contexto selado em desenvolvimento

## Hipótese

Após a correção do adaptador, os campos opcionais declarados no dataset devem
chegar ao `CompiledContext`, e nenhuma mutação nula pode ser contabilizada como
um desafio recusado ou aceito.

## Dataset e execução

O dataset público e integralmente sintético
`sealed_context_harness_development.json`, política
`sealed-context-harness-development-v1`, contém um controle e seis mutações.
Ele cobre página, seção, escopo, data de referência, associação de documento e
ordem global. Seu SHA-256 na execução foi
`928517530d72c7480c29148df7b1398552d4409e90583bcf0714bfde8151d7be`.

```bash
docker compose run --rm evaluate-sealed-context-harness
```

## Resultado

- correspondência exata: 100% (7/7);
- controle íntegro aceito: 1/1;
- mutações efetivas recusadas: 100% (6/6);
- todas as sete categorias atingiram 100%.

A suíte reconstruída passou com 227 testes; Ruff e mypy também passaram, com
160 arquivos analisados pelo mypy. O teste automatizado separado confirma que
o avaliador aborta, em vez de produzir métricas, quando uma mutação é nula.

## Decisão

O harness corrigido está aprovado no desenvolvimento para construir um novo
holdout. O resultado não reabilita o holdout inconclusivo, não promove o
renderer e não autoriza runtime, modelo local ou corpus privado. O próximo
conjunto deve ser novo, congelado por hash e executado uma única vez.
