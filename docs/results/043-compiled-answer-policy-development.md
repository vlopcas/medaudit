# Resultado 043: política explícita no request compilado

## Hipótese

A abstention excessiva observada no benchmark da aplicação poderia ser
corrigida levando a política `answer-when-supported-v1` para dentro do contexto
selado, sem alterar input, schema, temperatura, modelo ou limite de saída.

## Controle da variável

O gateway recebeu uma política explícita e opt-in. Um teste automatizado prova
que a candidata muda somente a instrução confiável antes da compilação; o
contexto sela essa escolha e o renderer mantém os demais campos idênticos.

Foram reutilizados apenas os quatro casos de desenvolvimento do Resultado 042,
sob o mesmo SHA-256
`4dfa15c1dc4b6f44044789958b5d4e2d63dae9efafeb146efa66a605f662fcfb`.
Nenhum holdout foi aberto.

```bash
docker compose run --rm benchmark-local-synthesis-application-answer-policy
```

## Resultado

- requests preparados e invocados: 100% (12/12);
- saídas grounded validadas: 25% (3/12);
- falhas do cliente: 75% (9/12);
- acurácia de status: 25% (3/12);
- conteúdo correto nos casos respondíveis: 0% (0/9);
- latência média: 5,94 s;
- pior latência: 8,27 s;
- as nove tentativas respondíveis terminaram em `client_failed` antes da
  validação grounded;
- as três abstentions realmente esperadas permaneceram válidas;
- 253 testes, Ruff e mypy passaram.

O relatório registra somente códigos genéricos e métricas. Nenhum texto gerado
foi persistido.

## Decisão

A política isolada foi rejeitada: ela remove o comportamento conservador, mas
o schema sem limites permite saídas que o adaptador não consegue materializar
dentro do teto de 512 tokens. A aplicação falhou fechada e não liberou nenhuma
dessas respostas.

O próximo experimento acrescentará somente o schema `bounded-v1`, já validado
em desenvolvimento anterior, mantendo a instrução candidata. Essa combinação
continua restrita a desenvolvimento sintético e não promove o modelo.
