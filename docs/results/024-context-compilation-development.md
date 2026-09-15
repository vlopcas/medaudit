# Resultado 024: compilação de contexto em desenvolvimento

## Hipótese e protocolo

Um compilador provider-neutral pode separar controle e dados não confiáveis,
aplicar orçamento e preservar provenance antes de qualquer renderização de
prompt. O protocolo `context-compilation-development-v1` usa um estimador
determinístico por palavras exclusivamente para tornar os budgets do benchmark
estáveis.

O dataset é integralmente sintético, tem SHA-256
`1b75dfa95b358d6e4eb6f92a9125ec6a69dc3ea29b9a38427139875b5314c9db` e
cobre seis categorias: contexto pronto, budget insuficiente para controle,
budget que elimina um passo, evidência em revisão, deduplicação entre passos e
evidência insuficiente.

## Resultados

| Métrica | Resultado |
|---|---:|
| Correspondência exata total | 100% (6/6) |
| Fronteira de confiança válida | 100% (6/6) |
| Categorias com 100% | 6/6 |

A correspondência exata exige simultaneamente estado, IDs incluídos, passos de
provenance, motivos de exclusão e confiança estrutural corretos. O relatório por
caso guarda apenas identificadores, estado, contagens e estimativas; um teste
automatizado confirma que o texto sintético das evidências não aparece nele.

Testes unitários adicionais cobrem identidade conflitante, revisão sem retenção
do trecho rejeitado e bloqueio quando o orçamento deixa algum passo sem suporte.

## Decisão

O contrato mínimo está aprovado somente em desenvolvimento e pode avançar para
holdout sintético inédito. Ele permanece fora do runtime, não renderiza prompts
e não chama LLM. A estimativa por palavras pertence apenas ao protocolo; a
implementação oferece uma interface substituível e uma aproximação padrão por
bytes.

O holdout deve acrescentar budgets nos limites exatos, múltiplas evidências por
passo, duplicatas em ordens diferentes, identidade conflitante e combinações de
revisão com orçamento. Nenhuma falha observada nesse holdout poderá ser usada
para ajustar esta candidata.

## Reprodução

```bash
docker compose run --rm evaluate-context-compilation
```
