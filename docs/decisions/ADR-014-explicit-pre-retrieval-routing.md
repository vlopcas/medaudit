# ADR-014: roteamento explícito antes do retrieval

## Status

Aceita em 2026-09-12.

## Contexto

Classificação lexical ampla, semântica local e heurísticas estruturais falharam
em seus respectivos conjuntos de avaliação. Ainda assim, existe valor em
impedir que consultas com dependência externa ou necessidade inequívoca de
planejamento sigam diretamente para uma única busca.

## Decisão

O runtime adota uma política estreita e determinística com três rotas:

- `requires_external_data` para dependências externas explícitas e atuais;
- `requires_decomposition` para comparação lexical explícita ou mais de uma
  data suportada na pergunta;
- `direct_retrieval` para todos os demais casos.

Dependência externa tem precedência. A política não acessa ferramentas, não
gera subconsultas e não usa intenção ampla para decidir a rota. O
`RoutedEvidenceFirstPipeline` chama o pipeline de evidências somente no caminho
direto; nas outras rotas, retorna sem tocar no retriever.

A política atingiu 100% em 18 casos de desenvolvimento e em 15 casos de holdout
congelado. Esses resultados medem conformidade com o contrato estreito, não
cobertura geral da linguagem natural.

## Consequências

- sinais ambíguos permanecem em retrieval direto por projeto;
- nenhuma indicação do LLM pode habilitar acesso externo;
- comparação e múltiplas datas não são tratadas incorretamente como consulta
  simples;
- executar decomposição e integrar ferramentas continuam trabalhos futuros.

## Como validar

- manter datasets sintéticos separados para desenvolvimento e holdout;
- validar precedência entre comparação e dependência externa;
- provar que rotas não diretas não carregam uma decisão de retrieval;
- recusar alterações no holdout por meio de SHA-256 e proteção de sobrescrita.
