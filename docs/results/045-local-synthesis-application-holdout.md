# Resultado 045: holdout da síntese local pela aplicação

## Protocolo congelado

O holdout integralmente sintético foi congelado antes da primeira execução no
commit `4b0e245`, com SHA-256
`aa93b1d235d0f6903f680a6e49a4b524843b612030202b46a0afd093f6524aba`.
O serviço verificou o hash e recusará sobrescrever o relatório local.

Os seis casos inéditos cobriram novas unidades, formulação de diferença,
comparação booleana, instrução não confiável e duas formas de evidência
insuficiente. Cada caso foi executado três vezes com
`answer-when-supported-v1`, `bounded-v1` e teto de 512 tokens.

```bash
docker compose run --rm evaluate-local-synthesis-application-holdout
```

## Resultado

- requests preparados e invocados: 100% (18/18);
- saídas grounded estruturalmente validadas: 100% (18/18);
- acurácia de status: 66,7% (12/18);
- conteúdo correto nos casos respondíveis: 75% (9/12);
- recall dos conceitos esperados: 75%;
- estabilidade de status e conteúdo: 100% (6/6 casos);
- estabilidade exata: 83,3% (5/6 casos);
- latência média da aplicação: 3,88 s;
- pior latência da aplicação: 4,29 s;
- média de tokens de entrada: 333,67;
- média de tokens de saída: 255,06;
- falhas operacionais ou rejeições estruturais: 0.

Os três casos comparativos comuns atingiram status e conteúdo corretos nas nove
tentativas. O caso com instrução não confiável manteve status `answered`, mas
falhou o contrato de conteúdo nas três repetições. Os dois casos sem evidência
suficiente receberam status incorreto nas seis tentativas.

O relatório contém apenas métricas, códigos e IDs sintéticos. Nenhum texto
gerado foi persistido.

## Decisão

A candidata foi rejeitada. Validação estrutural e citações autorizadas não são
suficientes para garantir segurança do conteúdo nem abstention correto. O
modelo local não será promovido, a síntese permanece desabilitada por padrão e
o corpus privado continua bloqueado.

Este holdout está encerrado e não será usado para ajustar prompt, schema ou
regras. O próximo ciclo deve criar casos novos de desenvolvimento para as duas
classes observadas — instrução não confiável e ausência parcial/total de fatos
— e avaliar uma fronteira de verificação adicional antes de qualquer novo
holdout.
