# Resultado 044: síntese compilada com schema limitado

## Hipótese

Adicionar somente os limites estruturais `bounded-v1` à política explícita de
resposta deveria impedir a expansão que causou nove falhas do cliente, sem
reintroduzir abstention excessiva.

## Controle da variável

O gateway passou a selecionar uma política de schema opt-in. A candidata
mantém modelo, dataset, instrução `answer-when-supported-v1`, input,
temperatura, limite de 512 tokens e três repetições. A única nova variável foi:

- até quatro claims;
- até 240 caracteres por claim;
- até quatro suportes por claim;
- até quatro citações por suporte.

Um teste automatizado confirma que input, instrução e temperatura permanecem
iguais ao baseline e que somente os limites do schema mudam. Foram reutilizados
apenas os quatro casos de desenvolvimento sob o SHA-256
`4dfa15c1dc4b6f44044789958b5d4e2d63dae9efafeb146efa66a605f662fcfb`.

```bash
docker compose run --rm benchmark-local-synthesis-application-bounded
```

## Resultado

- requests preparados: 100% (12/12);
- exatamente uma invocação por tentativa: 100% (12/12);
- saídas grounded validadas: 100% (12/12);
- acurácia de status: 100% (12/12);
- conteúdo correto nos casos respondíveis: 100% (9/9);
- recall dos conceitos esperados: 100%;
- falhas do cliente ou do contrato: 0;
- estabilidade exata, de status e de conteúdo: 100% (4/4 casos);
- latência média da aplicação: 3,01 s;
- pior latência da aplicação: 4,48 s;
- média de tokens de entrada: 320,75;
- média de tokens de saída: 188,75;
- 254 testes, Ruff e mypy passaram.

O relatório local preserva somente métricas, códigos e IDs sintéticos. Nenhum
prompt, evidência ou texto gerado foi persistido.

## Decisão

A combinação `answer-when-supported-v1` + `bounded-v1` + teto de 512 tokens
atingiu o gate de desenvolvimento através da aplicação completa. Isso não
promove o modelo, não habilita o caminho padrão e não libera o corpus privado.

O próximo marco é congelar um holdout sintético inédito específico dessa
configuração, registrar seu hash antes da primeira execução e recusar
sobrescrita do relatório. Os casos de desenvolvimento não serão usados como
evidência de promoção.
