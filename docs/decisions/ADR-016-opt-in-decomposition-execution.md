# ADR-016: execução opt-in de planos de decomposição

## Status

Aceita em 2026-09-13.

## Contexto

O planejador determinístico produz passos temporais ou comparativos, mas a
execução exige escolher corretamente o corpus. Em especial, reutilizar o
snapshot corrente para uma consulta histórica produziria evidência temporal
incorreta mesmo com um plano válido.

## Decisão

O `DeterministicDecompositionExecutor` executa cada passo isoladamente e recebe
duas dependências explícitas:

- um pipeline de evidências para escopos comparativos;
- um resolvedor que fornece o pipeline correspondente a cada data de snapshot.

O resultado preserva plano, passos e decisões de retrieval individuais. Todos
os passos precisam estar `ready` para a execução ficar `ready`; qualquer
abstention torna o agregado `insufficient_evidence`. Planos ambíguos permanecem
como `needs_clarification` e não executam retrieval.

O `RoutedEvidenceFirstPipeline` aceita o executor opcionalmente. Sem essa
configuração, continua retornando apenas o plano. Não existe fallback para o
snapshot corrente nem resolução implícita de datas.

O contrato atingiu 100% no desenvolvimento e no holdout sintético congelado,
incluindo exact match dos casos, documento por passo e isolamento dos passos
temporais.

## Consequências

- a integração é segura por configuração explícita e testável por injeção de
  dependências;
- evidências de versões temporais diferentes permanecem separadas;
- uma falha parcial não é mascarada por passos bem-sucedidos;
- combinação de evidências e geração comparativa continuam fora do executor.

## Como validar

- usar corpus e snapshots sintéticos independentes no holdout;
- medir status agregado e documento recuperado por passo em ordem;
- fixar `top_k`, limiar e SHA-256 antes de abrir o holdout;
- provar que a execução é ausente quando o executor não foi configurado.
