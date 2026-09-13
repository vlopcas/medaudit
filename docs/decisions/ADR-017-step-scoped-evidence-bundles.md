# ADR-017: pacotes de evidências preservam o escopo dos passos

## Status

Aceita em 2026-09-13.

## Contexto

Após executar uma decomposição, achatar resultados apagaria a associação entre
citação, escopo comparativo e data de referência. Isso permitiria misturar
versões ou usar evidência parcial como se todos os lados estivessem sustentados.

## Decisão

As evidências são agrupadas deterministicamente, em ordem, uma vez por passo.
Cada grupo conserva o `QueryPlanStep` completo e a sequência original de
evidências com suas localizações. Evidências repetidas em passos diferentes não
são deduplicadas, pois pertencem a contextos distintos.

O pacote só define `can_generate=true` quando a execução agregada está `ready`.
Evidência parcial continua disponível para inspeção, mas não autoriza síntese.
Um plano que precisa de esclarecimento produz pacote vazio e bloqueado.

Quando o `RoutedEvidenceFirstPipeline` recebe um executor opt-in, passa a
devolver automaticamente a execução e seu pacote agrupado. Sem executor,
continua devolvendo somente o plano.

## Consequências

- provenance temporal e comparativa atravessa a fronteira de retrieval;
- falhas parciais ficam visíveis sem serem promovidas a resposta;
- a etapa não resume, funde textos nem chama um LLM;
- uma futura síntese deverá consumir apenas pacotes com `can_generate=true`.

## Como validar

- medir exact match da estrutura agrupada;
- verificar contexto e citações em todos os grupos;
- incluir falha intermediária, esclarecimento e citação repetida no holdout;
- congelar o dataset por SHA-256 e recusar sobrescrita do resultado.
