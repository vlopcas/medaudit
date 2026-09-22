# Resultado 063: solicitação explícita de traversal

## Hipótese

Uma fronteira determinística conseguiria converter perguntas relacionais
explícitas em solicitações tipadas de traversal sem adivinhar referências
ausentes ou resolver aliases ambíguos.

## Estratégia e dataset

O compilador exige a palavra `caminho` e exatamente duas referências presentes
no catálogo revisado. IDs e aliases são comparados por igualdade textual com
limites de palavra. A ordem das menções define início e destino; somente a forma
explícita `caminho reverso` altera a direção. O limite permanece fixo em quatro
saltos.

Perguntas sem intenção de caminho ficam como `not_applicable`. Alias ambíguo,
referência ausente, desconhecida ou excedente produz `review`. Para não repetir
texto potencialmente sensível em telemetria, conjuntos não resolvidos usam um
marcador fechado.

O dataset `graph_request_development.json`, política
`graph-request-development-v1`, contém dez casos integralmente sintéticos. Seu
SHA-256 é
`3ac042f65eae3800c313287363d66f61295da7c4dad2c39cb52e4571b20b3063`.

```bash
docker compose run --rm evaluate-graph-request
```

## Resultado

- 10/10 compilações corresponderam exatamente ao esperado;
- IDs, aliases únicos, ordem das menções e direção reversa foram compilados;
- alias ambíguo e conjuntos incompletos, desconhecidos ou excessivos pararam em
  revisão;
- uma consulta sem intenção explícita não ativou o caminho de grafo;
- 303 testes passaram; Ruff passou e mypy não encontrou problemas em 211
  arquivos.

## Limitações

Esta política reconhece uma gramática intencionalmente estreita. Ela não faz
entity linking semântico, correção ortográfica, coreferência nem seleção de
relações. O catálogo de aliases continua sendo uma entrada revisada, não um
produto de extração automática.

## Decisão

A fronteira explícita pode ser composta ao traversal somente em
desenvolvimento sintético. O próximo experimento deve executar compilação e
traversal ponta a ponta e comparar a cadeia resultante ao BM25 usando as mesmas
perguntas e evidências. Graph RAG, holdout, banco de grafo e corpus privado
continuam bloqueados.
