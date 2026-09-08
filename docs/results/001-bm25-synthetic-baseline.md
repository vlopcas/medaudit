# Resultado 001: baseline BM25 sintético

## Hipótese

Uma implementação lexical simples deve recuperar corretamente códigos exatos e
termos compartilhados antes da introdução de embeddings ou geração por LLM.

## Dataset

- corpus integralmente sintético: 6 chunks;
- golden dataset integralmente sintético: 7 perguntas, incluindo um caso sem
  evidência;
- categorias iniciais: `exact_lookup`, `factual`, `exception` e
  `missing_evidence`;
- nenhuma dependência dos documentos privados locais.

## Configuração

- algoritmo: Okapi BM25;
- tokenização: minúsculas, remoção de acentos e preservação de códigos;
- parâmetros: `k1=1.5`, `b=0.75`;
- execução local, sem LLM e sem dependências externas.

## Resultados

| Métrica | K=1 | K=3 |
|---|---:|---:|
| Hit rate | 0,8333 | 1,0000 |
| Recall médio | 0,8333 | 1,0000 |
| MRR | 0,8333 | 0,9167 |

Sem limiar mínimo, a acurácia de abstention foi 0, pois termos genéricos do caso
sem resposta ainda produziram resultados. Com um limiar experimental de 3,0,
a acurácia de abstention foi 1,0 sem reduzir as métricas dos seis casos
respondíveis neste pequeno conjunto.

## Análise

O baseline recuperou em primeiro lugar cinco dos seis casos. Na pergunta sobre
a exceção de urgência, o chunk com a regra geral ficou à frente do chunk da
exceção porque ambos compartilham o mesmo código e vocabulário próximo. Esse é
um primeiro failure mode útil para comparar futuramente query expansion,
recuperação híbrida e reranking.

O conjunto ainda é pequeno e deliberadamente simples; os números não estimam
desempenho em documentos reais. Eles apenas validam o pipeline e estabelecem
uma medição reproduzível.

O limiar 3,0 foi ajustado sobre o mesmo conjunto e, portanto, não representa uma
estimativa generalizável. Quando o benchmark crescer, calibração e avaliação
deverão usar partições diferentes para evitar vazamento experimental.

## Reprodução

```bash
medaudit-evaluate-bm25 \
  --corpus data/synthetic_cases/corpus.json \
  --cases data/eval/bm25_cases.json \
  --top-k 3 \
  --min-score 3.0
```

## Decisão

Manter o BM25 como baseline lexical transparente. O próximo experimento deverá
aumentar a dificuldade do benchmark e adicionar casos sem resposta antes de
compará-lo com recuperação densa.
