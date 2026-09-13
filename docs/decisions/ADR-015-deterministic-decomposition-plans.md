# ADR-015: planos determinísticos de decomposição

## Status

Aceita em 2026-09-13.

## Contexto

O roteamento explícito já impede que comparações e consultas com múltiplas
datas sejam tratadas como uma única busca. Faltava transformar essa rota em um
plano inspecionável sem inventar escopos, acessar ferramentas ou executar
retrieval múltiplo prematuramente.

## Decisão

O `DeterministicQueryPlanner` aceita somente consultas previamente destinadas
a `requires_decomposition` e produz um dos seguintes resultados:

- `temporal_snapshots`: um passo por data explícita suportada, preservando a
  mesma consulta-base e associando uma única `reference_date` a cada passo;
- `comparison_scopes`: dois passos quando padrões sintáticos restritos isolam
  inequivocamente os dois lados da comparação;
- `needs_clarification`: nenhum passo quando os lados não podem ser separados
  com segurança.

Datas têm precedência sobre a separação lexical de comparação. Planos prontos
exigem ao menos dois passos; planos que pedem esclarecimento não podem conter
estratégia nem passos. O `RoutedEvidenceFirstPipeline` passa a devolver o plano
na rota de decomposição, mas não executa seus passos.

A política obteve 100% de exact match em 12 casos de desenvolvimento e 12 casos
de holdout sintético congelado.

## Consequências

- o chamador pode explicar por que a consulta foi dividida ou por que precisa
  de esclarecimento;
- nenhuma subconsulta inferida por significado é criada;
- o retriever continua intocado nas rotas não diretas;
- execução, combinação de evidências e síntese comparativa permanecem trabalhos
  futuros e exigirão avaliações próprias.

## Como validar

- avaliar status, estratégia, quantidade de passos, datas e escopos por exact
  match;
- manter desenvolvimento e holdout sintéticos separados;
- fixar o holdout por SHA-256 e recusar sobrescrita do relatório;
- testar que a decisão roteada contém plano, mas não evidências, na rota de
  decomposição.
