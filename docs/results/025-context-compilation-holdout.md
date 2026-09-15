# Resultado 025: holdout da compilação de contexto

## Hipótese e protocolo

O contrato aprovado em desenvolvimento deveria preservar decisões, provenance
e fronteiras de confiança em combinações inéditas. O holdout integralmente
sintético foi congelado antes da execução no commit `5baa05f`, com SHA-256
`5cc392586db4416715523d895de550ebc382c0d79051786419da9c396976e073`.

Oito categorias inéditas cobriram budget exatamente preenchido, múltiplas
evidências por passo, identidade compartilhada em ordem diferente, colisão de
identidade, precedência de revisão sobre budget, múltiplas revisões, duplicata
dentro do mesmo passo e precedência de evidência insuficiente. O comando exige
o hash congelado e recusa sobrescrever o primeiro relatório local.

## Resultados

| Métrica | Resultado |
|---|---:|
| Correspondência exata total | 100% (8/8) |
| Fronteira de confiança válida | 100% (8/8) |
| Categorias com 100% | 8/8 |

O caso de limite exato ocupou as 20 unidades disponíveis e permaneceu `ready`.
Identidade conflitante e revisão bloquearam o contexto; evidência insuficiente
teve precedência antes da seleção. Duplicatas foram excluídas sem perder a lista
de passos atendidos. O relatório contém somente IDs, estados, contagens e
estimativas, sem texto de evidência.

## Decisão

O contrato do compilador é promovido para integração opt-in ao caminho de
síntese decomposta. Isso não promove o modelo local, o detector de regex nem o
uso do corpus privado. A próxima mudança deve criar uma renderização do
`CompiledContext` para o contrato `LLMRequest`, provar equivalência estrutural e
manter toda chamada de modelo atrás de `can_generate`.

A seleção gulosa e o estimador aproximado continuam baselines simples. Packing,
compressão, reranking e tokenizer específico só serão adicionados após uma
limitação mensurável.

## Reprodução

A primeira execução já materializou o relatório protegido. Reexecutar deve
falhar em vez de sobrescrevê-lo:

```bash
docker compose run --rm evaluate-context-compilation-holdout
```
