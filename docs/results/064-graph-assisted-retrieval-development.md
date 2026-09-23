# Resultado 064: recuperação explícita assistida por grafo

## Hipótese

A composição pergunta → solicitação tipada → traversal recuperaria cadeias
relacionais completas que o BM25 não recupera, usando exatamente a mesma
pergunta em cada comparação e sem degradar abstention ou revisão.

## Estratégia e dataset

O `ExplicitGraphGateway` só executa traversal depois que o compilador valida uma
intenção de caminho e duas referências inequívocas. O resultado expõe quatro
estados fechados: `path_found`, `no_path`, `review` e `not_applicable`.

O dataset `graph_assisted_retrieval_development.json`, política
`graph-assisted-retrieval-development-v1`, contém sete casos integralmente
sintéticos. Quatro avaliam cadeias de dois, três e quatro saltos e impacto
reverso. Três controlam entidades desconectadas, alias ambíguo e consulta fora
do escopo. BM25 e gateway recebem a mesma pergunta e o mesmo conjunto de chunks
em cada caso. O SHA-256 do dataset é
`673e8a10046d9652f4b4b80df9982dff6b199ff78fa28ca87532f8475654ad11`.

```bash
docker compose run --rm evaluate-graph-assisted-retrieval
```

## Resultado

- BM25 recuperou a cadeia completa em 0/4 casos;
- o gateway recuperou a cadeia completa em 4/4 casos;
- os estados dos controles corresponderam ao esperado em 3/3 casos;
- toda aresta recuperada manteve documento e chunk de origem;
- a integração revelou e corrigiu uma colisão na qual o alias `ALFA` era
  reconhecido dentro do ID canônico `ALFA-1`;
- 309 testes passaram; Ruff passou e mypy não encontrou problemas em 215
  arquivos.

## Limitações

O slice é pequeno e adversarial, com distratores escolhidos para expor arestas
intermediárias ausentes na busca lexical. O resultado de 0% do BM25 não deve ser
generalizado para outras perguntas ou corpora.

O grafo já chega preenchido com entidades e relações revisadas; o experimento
não cobre extração, ETL, atualização, qualidade das relações, latência em escala
ou geração de resposta. As perguntas também usam uma gramática explícita com
dois endpoints, diferente das perguntas implícitas do benchmark inicial.

## Decisão

O gateway pode avançar para um holdout sintético inédito, ainda como caminho
experimental e opt-in. Antes de executar o holdout, dataset, hash, política e
artefato de saída devem ser congelados, com recusa de sobrescrita.

BM25 permanece como baseline padrão. Graph RAG, banco de grafo, extração
automática, respostas generativas e corpus privado continuam bloqueados.
