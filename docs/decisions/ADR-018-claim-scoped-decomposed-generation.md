# ADR-018: geração decomposta usa afirmações com suporte por passo

## Status

Aceita em 2026-09-13.

## Contexto

Uma resposta comparativa monolítica com uma lista global de citações não prova
qual evidência sustenta cada afirmação nem impede que uma citação de um lado
seja atribuída ao outro.

## Decisão

O contrato provider-neutral representa a resposta como `claims` atômicas. Cada
claim possui texto e um ou mais suportes formados por `step_id` e
`evidence_ids`. O validador resolve cada citação exclusivamente dentro do grupo
indicado e rejeita:

- passos desconhecidos ou citações pertencentes a outro grupo;
- claims vazias, sem suporte ou com duplicações;
- respostas `answered` que omitam algum grupo;
- abstention acompanhada de claims;
- geração a partir de pacote de evidências incompleto.

Uma afirmação pode cruzar grupos desde que declare separadamente o suporte de
cada passo. O request inclui texto somente das evidências autorizadas e trata
esse conteúdo como dado não confiável.

## Consequências

- a provenance é validável no nível da afirmação;
- comparações precisam representar todos os lados recuperados;
- o contrato permanece independente do fornecedor de LLM;
- aprovação estrutural não implica qualidade factual ou linguística do modelo.

## Como validar

- manter casos válidos e adversariais em desenvolvimento e holdout separados;
- exigir correspondência exata entre validade e categoria de erro esperadas;
- congelar o holdout por SHA-256 e recusar sobrescrita;
- avaliar o modelo local separadamente antes de integrá-lo ao runtime.
