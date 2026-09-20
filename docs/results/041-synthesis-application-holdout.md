# Resultado 041: holdout da aplicação de síntese

## Hipótese

A operação completa deveria preservar rota, preparação, segurança de invocação
e segurança de liberação diante de combinações inéditas de temporalidade,
revisão, budget, estados desabilitados e falhas posteriores à preparação.

## Protocolo

O holdout contém nove casos integralmente sintéticos sob a política
`synthesis-application-holdout-v1`. Instrumento, configuração e dataset foram
congelados no commit `242f729`, antes da execução, com SHA-256
`e2d6939111c599773e9b6265a4dfc5fafaeab4436ed526586b3eccebe22267d3`.

Antes da abertura, a suíte reconstruída passou com 250 testes, Ruff sem achados
e mypy sem problemas em 172 arquivos. O desenvolvimento permaneceu em 6/6 nas
três métricas. O holdout foi executado uma única vez, sem rede e com filesystem
da aplicação somente leitura. O relatório local está em
`artifacts/synthesis-application-holdout.local.json`, com recusa de
sobrescrita.

```bash
docker compose run --rm evaluate-synthesis-application-holdout
```

## Resultado

- correspondência exata: 100% (9/9);
- segurança de invocação: 100% (9/9);
- segurança de liberação: 100% (9/9);
- todas as nove categorias atingiram 100%;
- a decomposição temporal válida produziu resposta grounded validada;
- revisão, budget, rota externa e gateway desabilitado não chamaram o cliente;
- abstention válida foi liberada como resultado validado;
- step desconhecido e timeout terminaram sem resposta;
- o modo padrão permaneceu desabilitado mesmo diante de request preparado.

## Decisão

A composição completa está aprovada como arquitetura experimental e opt-in com
cliente falso. O comportamento padrão continua sem síntese e os contratos
anteriores permanecem inalterados.

O resultado comprova controle de fluxo e contratos, não qualidade factual de um
modelo. O próximo marco é um benchmark de compatibilidade do modelo local por
essa aplicação, somente com dados sintéticos e sem abrir novo holdout. Corpus
privado e ativação no runtime permanecem bloqueados; qualquer promoção exige
métricas explícitas de conteúdo, grounding, repetibilidade e latência.
