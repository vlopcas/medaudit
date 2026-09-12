# Plano Completo de Estudos e Projeto --- LLM, RAG, GraphRAG e Agentes

> O progresso da implementação é acompanhado separadamente em
> [Status do plano de estudos](study-progress.md). Este arquivo permanece como
> roteiro conceitual e não deve ser interpretado como uma lista linear do que já
> foi concluído.

> Objetivo: sair dos fundamentos e chegar à construção de um sistema
> robusto de auditoria documental, capaz de consultar documentos,
> correlacionar regras, acessar dados estruturados, interpretar conteúdo
> multimodal, justificar conclusões com evidências e operar com métricas
> de qualidade, custo e latência.

## 0. Estratégia do projeto

Este plano usa **um único projeto principal evolutivo**, com os mesmos
documentos e um benchmark relativamente estável. Pequenos projetos
separados são usados apenas como *spikes* para aprender ou comparar uma
tecnologia.

Princípio central:

**não adicionar complexidade antes de medir a limitação que ela
resolve.**

A evolução será:

``` text
Fundamentos
  ↓
RAG básico
  ↓
Evaluation
  ↓
Parsing/document intelligence
  ↓
Hybrid retrieval
  ↓
Reranking
  ↓
Structured knowledge/rules
  ↓
Knowledge Graph / GraphRAG
  ↓
Tool calling + bancos/APIs
  ↓
Agentic workflow
  ↓
Multimodal
  ↓
Observability + segurança
  ↓
Performance
  ↓
Sistema final
```

------------------------------------------------------------------------

# 1. Projeto-guia

## Caso de uso

Construir progressivamente um **agente de auditoria baseado em
documentos**.

No estágio final, o sistema deverá conseguir:

1.  receber uma pergunta ou caso;
2.  identificar quais dados são necessários;
3.  recuperar normas e documentos relevantes;
4.  correlacionar regras distribuídas em documentos diferentes;
5.  considerar versão e vigência das normas;
6.  consultar banco de dados e/ou APIs;
7.  interpretar texto, tabelas, imagens e diagramas;
8.  aplicar regras e exceções;
9.  detectar evidência ausente ou contraditória;
10. produzir conclusão;
11. citar precisamente as fontes utilizadas;
12. manter um audit trail;
13. informar incerteza em vez de inventar;
14. ser avaliado automaticamente;
15. ter custo e latência mensuráveis.

> Para um domínio médico real, decisões de alta consequência devem
> permanecer sujeitas a validação humana e aos requisitos regulatórios
> aplicáveis. O projeto de estudo pode usar dados sintéticos ou
> devidamente desidentificados.

------------------------------------------------------------------------

# 2. Estrutura inicial do repositório

``` text
llm-audit-system/
├── README.md
├── pyproject.toml
├── .env.example
├── docker-compose.yml
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── synthetic_cases/
│   └── eval/
│
├── src/
│   ├── llm/
│   ├── ingestion/
│   ├── parsing/
│   ├── chunking/
│   ├── embeddings/
│   ├── retrieval/
│   ├── reranking/
│   ├── knowledge/
│   ├── graph/
│   ├── rules/
│   ├── tools/
│   ├── agents/
│   ├── evaluation/
│   ├── observability/
│   └── api/
│
├── experiments/
│   ├── 01_llm_basics/
│   ├── 02_embeddings/
│   ├── 03_basic_rag/
│   ├── 04_chunking/
│   ├── 05_hybrid/
│   ├── 06_reranking/
│   ├── 07_graph/
│   └── 08_agentic/
│
├── tests/
└── docs/
    ├── architecture.md
    ├── decisions/
    └── results/
```

## Regra de engenharia

Cada evolução relevante deve registrar:

-   hipótese;
-   baseline;
-   mudança implementada;
-   dataset utilizado;
-   métricas antes;
-   métricas depois;
-   custo;
-   latência;
-   conclusão.

Não manter uma feature apenas porque "parece melhor".

------------------------------------------------------------------------

# 3. Fase 0 --- Preparação

## Objetivos

Preparar Python, Git, ambiente e disciplina experimental.

## Estudar

-   Python moderno;
-   virtual environments;
-   typing;
-   `async`/`await`;
-   HTTP e APIs;
-   JSON;
-   Pydantic/dataclasses;
-   SQL básico;
-   Git;
-   Docker básico;
-   testes automatizados;
-   variáveis de ambiente.

## Prática

Criar um programa que:

1.  recebe texto;
2.  chama um LLM;
3.  exige resposta estruturada;
4.  valida a resposta;
5.  registra tokens, latência e erro.

## Critério para avançar

Você consegue explicar:

-   request/response;
-   tokens;
-   temperatura;
-   context window;
-   structured output;
-   retry;
-   timeout;
-   rate limit.

------------------------------------------------------------------------

# 4. Fase 1 --- Fundamentos de LLMs

## Estudar

### Tokens

Entender:

-   tokenização;
-   input/output tokens;
-   contexto;
-   impacto no custo e latência.

### Transformers

Entender conceitualmente:

-   embeddings;
-   self-attention;
-   positional information;
-   transformer blocks;
-   logits;
-   sampling.

Não é necessário implementar um Transformer completo.

### Inferência

Estudar:

-   temperature;
-   top-p;
-   deterministic vs probabilistic output;
-   context window;
-   hallucination;
-   instruction hierarchy;
-   structured outputs.

### Prompting

Aprender:

-   system/instructions;
-   few-shot;
-   delimitadores;
-   schemas;
-   decomposição de tarefas;
-   geração fundamentada em evidência.

## Experimentos

Criar scripts para:

-   classificação;
-   extração estruturada;
-   sumarização;
-   resposta usando contexto fornecido;
-   comparação de prompts.

## Resultado esperado

Entender o LLM como **componente probabilístico**, não como banco de
dados.

------------------------------------------------------------------------

# 5. Fase 2 --- Embeddings e Information Retrieval

Esta fase é essencial.

## Estudar embeddings

Conceitos:

-   vetor;
-   dimensionalidade;
-   cosine similarity;
-   dot product;
-   nearest neighbors;
-   semantic similarity.

## Implementar

Começar sem framework:

``` text
10–50 textos
   ↓
embeddings
   ↓
armazenar vetores
   ↓
embedding da pergunta
   ↓
similaridade
   ↓
top-k
```

## Depois estudar

-   approximate nearest neighbors;
-   HNSW;
-   vector indexes;
-   filtros por metadata.

## Retrieval clássico

Aprender também:

-   inverted index;
-   TF-IDF;
-   BM25.

Pergunta importante:

**quando busca lexical supera busca semântica?**

Exemplos:

-   código de norma;
-   nome exato;
-   número de procedimento;
-   artigo;
-   identificadores.

## Critério para avançar

Você consegue explicar por que:

``` text
BM25 != embeddings
```

e quais consultas favorecem cada abordagem.

------------------------------------------------------------------------

# 6. Fase 3 --- Primeiro RAG

## Pipeline

``` text
documentos
   ↓
parser
   ↓
chunks
   ↓
embeddings
   ↓
vector index

pergunta
   ↓
embedding
   ↓
retrieval
   ↓
top-k chunks
   ↓
prompt
   ↓
LLM
   ↓
resposta + fontes
```

## Implementar inicialmente

-   20--50 documentos;
-   parsing simples;
-   chunking;
-   embeddings;
-   vector search;
-   top-k;
-   prompt baseado somente nas evidências;
-   referências aos documentos.

## Metadados obrigatórios

Cada chunk deve carregar algo como:

``` json
{
  "document_id": "...",
  "document_name": "...",
  "version": "...",
  "page": 12,
  "section": "...",
  "chunk_id": "...",
  "effective_date": "...",
  "expiration_date": "..."
}
```

## Testes

Perguntas:

-   factuais;
-   semânticas;
-   referência exata;
-   resposta inexistente.

O sistema precisa ser capaz de dizer:

> evidência insuficiente.

------------------------------------------------------------------------

# 7. Fase 4 --- Evaluation desde cedo

Não espere o projeto ficar grande.

## Criar golden dataset

Começar com 30--50 casos e crescer progressivamente.

Estrutura possível:

``` json
{
  "id": "case_001",
  "question": "...",
  "expected_answer": "...",
  "relevant_documents": ["doc_1", "doc_3"],
  "relevant_chunks": [],
  "required_rules": [],
  "category": "multi_hop"
}
```

## Categorias

-   factual;
-   exact lookup;
-   semantic;
-   multi-document;
-   multi-hop;
-   temporal;
-   conflicting rules;
-   missing evidence;
-   table;
-   image;
-   external-data.

## Métricas de retrieval

Estudar:

-   Precision@K;
-   Recall@K;
-   MRR;
-   nDCG;
-   hit rate.

## Métricas de geração

Avaliar:

-   correctness;
-   groundedness/faithfulness;
-   completeness;
-   citation correctness;
-   abstention correctness.

## Métricas operacionais

Registrar:

-   latency;
-   tokens;
-   custo;
-   erros;
-   número de retrievals;
-   chamadas de LLM.

------------------------------------------------------------------------

# 8. Fase 5 --- Document parsing e chunking

Aqui começa a engenharia documental séria.

## Comparar estratégias de chunking

### Fixed-size

Ex.:

``` text
500 tokens + overlap
```

### Recursive

Separar por:

-   seção;
-   parágrafo;
-   sentença.

### Semantic chunking

Separar considerando mudança de assunto.

### Structure-aware

Preservar:

``` text
documento
└── capítulo
    └── seção
        └── subseção
            └── parágrafo
```

## Experimento obrigatório

Comparar pelo menos três estratégias usando o mesmo benchmark.

Medir:

``` text
Recall@5
Recall@10
MRR
latência
tamanho médio do contexto
```

## Problemas a estudar

-   chunks pequenos demais;
-   chunks grandes demais;
-   overlap;
-   contexto perdido;
-   títulos separados do conteúdo;
-   listas;
-   notas;
-   cabeçalhos/rodapés.

------------------------------------------------------------------------

# 9. Fase 6 --- Hybrid Retrieval

Construir:

``` text
query
 ├── BM25
 └── dense retrieval
       ↓
     fusion
       ↓
     top-k
```

## Estudar

-   score normalization;
-   Reciprocal Rank Fusion (RRF);
-   metadata filters;
-   query expansion;
-   query rewriting;
-   multi-query retrieval.

## Comparação obrigatória

``` text
BM25
vs
Dense
vs
Hybrid
```

Separar resultados por categoria de pergunta.

------------------------------------------------------------------------

# 10. Fase 7 --- Reranking

Pipeline:

``` text
query
  ↓
retrieval amplo
  ↓
20–100 candidatos
  ↓
reranker
  ↓
5–10 evidências
  ↓
LLM
```

## Estudar

-   cross-encoders;
-   LLM reranking;
-   relevância vs custo;
-   top-k inicial;
-   top-n final.

## Experimento

Comparar:

``` text
Hybrid
vs
Hybrid + reranker
```

Medir qualidade, custo e latência.

------------------------------------------------------------------------

# 11. Fase 8 --- Query Understanding

Nem toda pergunta deve ir diretamente ao retriever.

Criar uma etapa capaz de identificar:

``` json
{
  "intent": "audit_case",
  "entities": [],
  "date": null,
  "procedure": null,
  "plan": null,
  "requires_external_data": true
}
```

## Estudar

-   intent classification;
-   entity extraction;
-   query rewriting;
-   decomposition;
-   subqueries.

Exemplo:

``` text
Pergunta complexa
     ↓
subquestion 1
subquestion 2
subquestion 3
     ↓
retrieval individual
     ↓
evidence aggregation
```

Isso prepara o terreno para multi-hop e agentes.

------------------------------------------------------------------------

# 12. Fase 9 --- Regras estruturadas

Não deixe toda lógica crítica exclusivamente dentro de texto natural.

## Criar modelo de regra

Exemplo:

``` json
{
  "rule_id": "R-017",
  "subject": "procedure_x",
  "conditions": [
    {
      "field": "age",
      "operator": ">=",
      "value": 18
    }
  ],
  "exceptions": [],
  "valid_from": "2026-01-01",
  "valid_until": null,
  "source": {
    "document_id": "...",
    "page": 17,
    "section": "4.2"
  }
}
```

## Pipeline

``` text
documento
   ↓
extração pelo LLM
   ↓
schema estruturado
   ↓
validação
   ↓
rule store
   ↓
revisão humana quando necessário
```

## Estudar

-   information extraction;
-   schema design;
-   validation;
-   deterministic rule execution;
-   provenance.

## Regra arquitetural

Use LLM para:

-   interpretação;
-   extração;
-   planejamento;
-   explicação.

Prefira software determinístico para:

-   cálculos;
-   comparação de valores;
-   execução de regras formalizadas;
-   validação de schema.

------------------------------------------------------------------------

# 13. Fase 10 --- Temporalidade e versionamento

Essencial para normas.

Representar:

``` text
document_id
version
published_at
effective_from
effective_until
supersedes
jurisdiction
organization
plan
```

## Testes

Criar perguntas como:

> Qual regra era aplicável em 12/03/2024?

O retrieval deve filtrar versões incompatíveis antes da geração quando
possível.

## Casos difíceis

-   norma revogada;
-   norma parcialmente substituída;
-   exceção criada posteriormente;
-   conflito de vigência;
-   ausência de data.

------------------------------------------------------------------------

# 14. Fase 11 --- Knowledge Graph

Só agora introduzir grafo.

## Estudar fundamentos

-   nodes;
-   edges;
-   properties;
-   graph traversal;
-   Cypher;
-   ontologias;
-   entity resolution.

## Modelo inicial

``` text
[Document]
    │ contains
    ▼
[Rule]
    │ applies_to
    ▼
[Procedure]

[Rule]
    │ has_exception
    ▼
[Exception]

[Rule B]
    │ supersedes
    ▼
[Rule A]
```

## Entidades possíveis

-   documento;
-   regra;
-   procedimento;
-   condição;
-   exceção;
-   diagnóstico;
-   plano;
-   organização;
-   versão;
-   data.

## Não fazer

Não transformar tudo em grafo indiscriminadamente.

O grafo deve representar relações que realmente ajudam consultas e
reasoning.

------------------------------------------------------------------------

# 15. Fase 12 --- Graph-assisted RAG / GraphRAG

Agora comparar:

``` text
Vector retrieval
Hybrid retrieval
Graph retrieval
Hybrid + Graph
```

## Perguntas adequadas

-   quais regras afetam X?;
-   quais exceções dependem de Y?;
-   qual norma substituiu esta?;
-   quais regras conectam procedimento A à condição B?;
-   quais documentos participam desta decisão?

## Multi-hop

Exemplo:

``` text
Procedure X
  ↓
Rule A
  ↓
Exception B
  ↓
Condition C
  ↓
Rule D
```

O sistema deve recuperar a cadeia e preservar a fonte de cada passo.

## Critério de sucesso

Graph retrieval precisa melhorar especialmente:

-   multi-hop;
-   conflitos;
-   relações;
-   dependências.

Se não melhorar o benchmark, não presumir que o grafo é necessário.

------------------------------------------------------------------------

# 16. Fase 13 --- Tool Calling

Agora conectar o LLM ao mundo externo.

## Criar tools específicas

``` text
get_patient()
get_procedure()
get_exam()
get_plan()
get_claim()
search_rules()
get_rule_source()
execute_rule()
```

## Evitar inicialmente

``` text
execute_arbitrary_sql()
```

Prefira interfaces restritas.

## Estudar

-   function/tool calling;
-   schemas;
-   validation;
-   permissions;
-   retries;
-   idempotency;
-   timeouts;
-   error handling.

## Segurança

Separar:

``` text
read tools
write tools
privileged tools
```

Um agente de auditoria normalmente deve possuir acesso mínimo
necessário.

------------------------------------------------------------------------

# 17. Fase 14 --- Bancos de dados e APIs

Criar um banco sintético.

## Tabelas possíveis

``` text
patients
claims
procedures
exams
plans
providers
authorizations
```

## Exercício

Pergunta:

> O caso 123 atende aos critérios da regra vigente?

Pipeline:

``` text
caso
 ↓
dados necessários
 ↓
DB
 ↓
facts
 ↓
regras aplicáveis
 ↓
rule evaluation
 ↓
evidências
 ↓
conclusão
```

## Conceitos

-   SQL;
-   joins;
-   transactions;
-   connection pooling;
-   authorization;
-   row-level access;
-   data validation.

------------------------------------------------------------------------

# 18. Fase 15 --- Agentes

Agora estudar agentes de fato.

Modelo mental:

``` text
state
  ↓
reason
  ↓
select action
  ↓
tool
  ↓
observation
  ↓
update state
  ↓
next action
```

## Antes de LangGraph

Implementar um pequeno loop manual para entender:

-   state;
-   messages;
-   tools;
-   termination;
-   max steps;
-   failures.

## Problemas que devem ficar claros

-   loop infinito;
-   tool errada;
-   argumentos inválidos;
-   contexto crescendo;
-   ações repetidas;
-   reasoning desnecessário.

------------------------------------------------------------------------

# 19. Fase 16 --- LangGraph

Somente agora usar framework de orquestração.

Workflow possível:

``` text
START
  ↓
parse_request
  ↓
load_case
  ↓
identify_required_facts
  ↓
retrieve_rules
  ↓
enough_evidence?
  ├── no → retrieve_more
  │          ↓
  │      query_external_data
  │          ↓
  └──────────┘
  ↓
apply_rules
  ↓
detect_conflicts
  ↓
verify_sources
  ↓
generate_report
  ↓
final_validation
  ↓
END
```

## Estudar

-   state;
-   nodes;
-   edges;
-   conditional edges;
-   persistence;
-   checkpoints;
-   retries;
-   interrupts;
-   human-in-the-loop.

## Objetivo

Usar LangGraph porque o workflow necessita controle --- não porque
agentes estão em alta.

------------------------------------------------------------------------

# 20. Fase 17 --- Agentic RAG

Agora unir retrieval e planejamento.

O agente pode:

``` text
1. entender a pergunta;
2. decompor;
3. procurar regra;
4. descobrir referência a outra norma;
5. buscar essa norma;
6. consultar dado real;
7. perceber informação faltante;
8. realizar nova busca;
9. aplicar regra;
10. verificar evidências;
11. responder.
```

## Guardrails

Definir:

-   máximo de passos;
-   máximo de custo;
-   timeout;
-   ferramentas permitidas;
-   critérios de término;
-   comportamento diante de evidência insuficiente.

------------------------------------------------------------------------

# 21. Fase 18 --- Multimodal Document Intelligence

Agora atacar PDFs complexos.

## Tipos de conteúdo

-   texto;
-   scan;
-   tabela;
-   imagem;
-   gráfico;
-   diagrama;
-   formulário;
-   assinatura;
-   cabeçalho;
-   rodapé.

## Pipeline

``` text
PDF
 ↓
layout analysis
 ↓
classificação de elementos
 ├── text
 ├── title
 ├── table
 ├── figure
 ├── diagram
 └── footer
 ↓
extração especializada
 ↓
representação estruturada
 ↓
indexação
```

## Tabelas

Preservar estrutura:

``` text
headers
rows
columns
cells
page
caption
```

Evitar simplesmente concatenar todas as células.

## Imagens/diagramas

Usar modelo multimodal quando a informação visual for semanticamente
necessária.

Guardar:

``` text
image_id
document_id
page
caption
description
related_section
```

## Evaluation multimodal

Criar perguntas que só podem ser respondidas corretamente se:

-   tabela for interpretada;
-   gráfico for lido;
-   diagrama for compreendido;
-   relação texto-imagem for preservada.

------------------------------------------------------------------------

# 22. Fase 19 --- Provenance e citações

Cada afirmação importante deve ser rastreável.

Estrutura desejada:

``` text
Conclusion
 ├── claim 1
 │    ├── rule R17
 │    └── doc X, page 18, section 4.2
 │
 ├── claim 2
 │    ├── patient fact
 │    └── database record
 │
 └── claim 3
      └── rule R29
           └── doc Y, page 31
```

## Guardar

-   source;
-   document;
-   version;
-   page;
-   section;
-   chunk;
-   retrieval score;
-   rule;
-   database fact;
-   timestamp.

## Teste

Para cada conclusão:

> consigo reconstruir por que o sistema chegou nisso?

Se não, o audit trail está incompleto.

------------------------------------------------------------------------

# 23. Fase 20 --- Verifier

Adicionar etapa independente de verificação.

``` text
draft conclusion
       ↓
verifier
       ↓
checks:
- cada claim possui evidência?
- evidência suporta o claim?
- regra está vigente?
- há conflito ignorado?
- dado do banco corresponde ao caso?
- conclusão extrapola a fonte?
       ↓
pass / retry / human review
```

O verifier não deve simplesmente repetir o mesmo prompt do gerador.

------------------------------------------------------------------------

# 24. Fase 21 --- Human-in-the-loop

Para decisões críticas:

``` text
AI
 ↓
evidence package
 ↓
confidence / risk
 ↓
human reviewer
 ↓
approve / reject / correct
```

Registrar correções humanas para:

-   debugging;
-   novos casos de avaliação;
-   análise de falhas;
-   melhoria futura.

------------------------------------------------------------------------

# 25. Fase 22 --- Observability

Instrumentar desde cedo, aprofundar aqui.

Cada execução deve ter um `trace_id`.

Registrar:

``` text
query
retrievals
documents returned
scores
reranking
tool calls
LLM calls
tokens
latency
cost
errors
final citations
```

## Dashboards

Acompanhar:

-   p50/p95 latency;
-   custo médio;
-   retrieval recall;
-   answer accuracy;
-   citation accuracy;
-   tool error rate;
-   abstention rate.

------------------------------------------------------------------------

# 26. Fase 23 --- Performance

Só otimizar depois de medir.

## Técnicas

### Parallel retrieval

``` text
             ┌─ BM25
query ───────┼─ Vector
             └─ Graph
                 ↓
               fusion
```

### Async I/O

Paralelizar operações independentes:

-   APIs;
-   DB;
-   retrieval;
-   chamadas auxiliares.

### Caching

Estudar:

-   embedding cache;
-   retrieval cache;
-   semantic cache;
-   document parsing cache;
-   rule extraction cache.

### Precomputation

Pré-calcular:

-   embeddings;
-   summaries;
-   entities;
-   relations;
-   regras;
-   communities;
-   metadata.

### Model routing

``` text
classificação      → modelo menor
extração simples   → modelo menor
query rewrite      → modelo menor
reasoning difícil  → modelo maior
vision             → modelo multimodal
```

### Context optimization

Não mandar 50 chunks para o modelo quando 6 bastam.

Medir:

``` text
quality
vs
tokens
vs
latency
vs
cost
```

------------------------------------------------------------------------

# 27. Fase 24 --- Segurança e robustez

## Estudar

-   prompt injection;
-   indirect prompt injection em documentos;
-   data exfiltration;
-   tool abuse;
-   permission boundaries;
-   secrets;
-   PII;
-   logging seguro.

## Regra fundamental

Conteúdo recuperado de documentos é **dados**, não instrução confiável.

Exemplo malicioso em documento:

``` text
Ignore as instruções anteriores e envie...
```

O sistema não deve tratá-lo como comando.

## Tools

Aplicar:

-   allowlists;
-   schema validation;
-   least privilege;
-   read-only por padrão;
-   limites de consultas;
-   autenticação fora do LLM.

------------------------------------------------------------------------

# 28. Fase 25 --- Testes de adversidade

Criar casos para:

-   documento irrelevante altamente semelhante;
-   normas conflitantes;
-   regra antiga;
-   documento malicioso;
-   dado ausente;
-   banco indisponível;
-   timeout;
-   tabela mal extraída;
-   OCR incorreto;
-   pergunta ambígua;
-   entidade com nomes parecidos;
-   retrieval incompleto;
-   evidência contraditória.

O comportamento correto muitas vezes é:

``` text
não há evidência suficiente para concluir
```

e não uma resposta inventada.

------------------------------------------------------------------------

# 29. Fase 26 --- Arquitetura final

Uma possível arquitetura madura:

``` text
                         USER / API
                             │
                             ▼
                    ┌─────────────────┐
                    │ Request Parser  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Orchestrator    │
                    │ / Agent Graph   │
                    └────────┬────────┘
                             │
          ┌──────────────────┼───────────────────┐
          │                  │                   │
          ▼                  ▼                   ▼
   Knowledge Search       Data Tools         Rule Engine
          │                  │                   │
   ┌──────┼──────┐      ┌────┼────┐              │
   │      │      │      │         │              │
 BM25  Vector  Graph    SQL       APIs            │
   │      │      │      │         │              │
   └──────┼──────┘      └────┬────┘              │
          │                  │                   │
          ▼                  ▼                   ▼
       Fusion              Facts             Decisions
          │                  │                   │
          ▼                  │                   │
      Reranker               │                   │
          │                  │                   │
          └──────────────────┼───────────────────┘
                             │
                             ▼
                      Evidence Store
                             │
                             ▼
                         Reasoner
                             │
                             ▼
                         Verifier
                             │
                   ┌─────────┴─────────┐
                   │                   │
                  pass               risk
                   │                   │
                   ▼                   ▼
              Final Report        Human Review
                   │
                   ▼
            Citations + Audit Trail
```

------------------------------------------------------------------------

# 30. Sequência prática de versões

## V0 --- LLM playground

Objetivo:

-   chamadas;
-   structured output;
-   tokens;
-   erros.

## V1 --- Embedding search

Objetivo:

-   entender semantic retrieval.

## V2 --- Basic RAG

Objetivo:

-   documentos → chunks → busca → resposta.

## V3 --- RAG + evaluation

Objetivo:

-   criar benchmark antes de sofisticar.

## V4 --- Better chunking

Objetivo:

-   medir impacto da segmentação.

## V5 --- Hybrid RAG

Objetivo:

-   BM25 + dense.

## V6 --- Reranking

Objetivo:

-   melhorar precisão do contexto final.

## V7 --- Query intelligence

Objetivo:

-   rewrite, decomposition e metadata filters.

## V8 --- Structured rules

Objetivo:

-   transformar regras importantes em estruturas executáveis.

## V9 --- Temporal RAG

Objetivo:

-   versionamento e vigência.

## V10 --- Knowledge Graph

Objetivo:

-   relações explícitas.

## V11 --- Graph-assisted RAG

Objetivo:

-   multi-hop.

## V12 --- Database tools

Objetivo:

-   correlacionar documentos com dados reais/sintéticos.

## V13 --- Agent

Objetivo:

-   decidir quais ações executar.

## V14 --- LangGraph

Objetivo:

-   controlar workflow, estado e retries.

## V15 --- Multimodal

Objetivo:

-   tabelas, imagens e diagramas.

## V16 --- Verifier + provenance

Objetivo:

-   decisão auditável.

## V17 --- Observability

Objetivo:

-   entender cada execução.

## V18 --- Performance

Objetivo:

-   custo e latência.

## V19 --- Security/adversarial tests

Objetivo:

-   comportamento robusto.

## V20 --- Production-like system

Objetivo:

-   API, testes, deployment e monitoramento.

------------------------------------------------------------------------

# 31. Como usar Codex durante o projeto

O Codex deve acelerar a implementação, não substituir seu aprendizado.

## Formato de missão

Para cada tarefa, forneça:

``` text
Contexto:
[arquitetura atual]

Objetivo:
[uma mudança específica]

Restrições:
[não alterar X, usar Y...]

Critérios de aceite:
[testes e comportamento]

Evaluation:
[métrica que precisa ser comparada]

Documentação:
[registrar decisão e explicar implementação]
```

## Exemplo

``` text
MISSÃO: adicionar BM25 ao retrieval.

Antes de implementar:
1. analise o retrieval atual;
2. explique onde BM25 entrará;
3. proponha interfaces;
4. não altere o vector retriever existente.

Implemente:
- BM25Retriever;
- Reciprocal Rank Fusion;
- testes unitários;
- benchmark comparando dense, BM25 e hybrid.

Critérios:
- testes passam;
- benchmark reproduzível;
- resultados gravados em docs/results/.
```

## Depois de cada missão

Peça ao Codex:

``` text
Explique:

1. quais arquivos foram alterados;
2. por que foram alterados;
3. fluxo de dados;
4. principais decisões arquiteturais;
5. failure modes;
6. complexidade;
7. como testar;
8. o que eu preciso entender antes de continuar.
```

## Regra

Não avance enquanto você não conseguir explicar a implementação em alto
nível sem consultar o código.

------------------------------------------------------------------------

# 32. Git

Criar tags/releases importantes:

``` text
v0.1-basic-rag
v0.2-evaluation
v0.3-hybrid
v0.4-reranker
v0.5-rules
v0.6-graph
v0.7-tools
v0.8-agent
v0.9-multimodal
v1.0
```

Branches curtas por experimento.

Não criar branches eternas representando cada versão do sistema.

------------------------------------------------------------------------

# 33. ADRs --- Architecture Decision Records

Registrar decisões relevantes.

Exemplo:

``` text
ADR-001: escolha do vector database
ADR-002: estratégia de chunking
ADR-003: hybrid retrieval
ADR-004: reranker
ADR-005: modelagem temporal
ADR-006: knowledge graph
ADR-007: rule engine
ADR-008: agent orchestration
```

Formato:

``` markdown
# ADR-XXX

## Contexto

## Opções consideradas

## Decisão

## Consequências

## Como validar
```

Isso força você a pensar como engenheiro e não apenas integrar
bibliotecas.

------------------------------------------------------------------------

# 34. O que não priorizar no começo

Não gastar energia inicialmente com:

-   multi-agent;
-   fine-tuning;
-   treinamento de LLM;
-   Kubernetes;
-   GraphRAG antes do baseline;
-   framework complexo de agentes;
-   interface bonita;
-   otimizações prematuras.

Primeiro:

``` text
retrieval
+
evaluation
+
document understanding
+
grounding
```

------------------------------------------------------------------------

# 35. Quando estudar fine-tuning

Somente depois de entender claramente o problema.

Fine-tuning pode ser útil para:

-   comportamento;
-   estilo;
-   classificação especializada;
-   extração repetitiva;
-   formatos específicos;
-   modelos menores especializados.

Não é substituto natural para conhecimento documental atualizado.

Para conhecimento dinâmico:

``` text
RAG / DB / tools
```

normalmente continuam necessários.

------------------------------------------------------------------------

# 36. Conhecimentos paralelos importantes

Ao longo do projeto estudar também:

## Software engineering

-   clean architecture;
-   interfaces;
-   dependency injection;
-   testing;
-   logging;
-   configuration;
-   async;
-   profiling.

## Data engineering

-   ETL;
-   schemas;
-   migrations;
-   data quality;
-   lineage;
-   versioning.

## Information retrieval

-   BM25;
-   dense retrieval;
-   ranking;
-   reranking;
-   relevance evaluation.

## ML/LLM evaluation

-   datasets;
-   baselines;
-   metrics;
-   experiments;
-   error analysis.

## Backend

-   REST;
-   authentication;
-   databases;
-   caching;
-   queues;
-   concurrency.

O sistema final é muito mais **software + data + IR + LLM** do que
simplesmente "prompt engineering".

------------------------------------------------------------------------

# 37. Matriz de experimentos

Manter tabela semelhante a:

  --------------------------------------------------------------------------------------------------------
  Versão   Retrieval   Reranker   Graph   Agent   Multimodal     Recall@10   Multi-hop   Latência    Custo
  -------- ----------- ---------- ------- ------- ------------ ----------- ----------- ---------- --------
  V3       Dense       Não        Não     Não     Não                  ---         ---        ---      ---

  V5       Hybrid      Não        Não     Não     Não                  ---         ---        ---      ---

  V6       Hybrid      Sim        Não     Não     Não                  ---         ---        ---      ---

  V11      Hybrid      Sim        Sim     Não     Não                  ---         ---        ---      ---

  V14      Hybrid      Sim        Sim     Sim     Não                  ---         ---        ---      ---

  V16      Hybrid      Sim        Sim     Sim     Sim                  ---         ---        ---      ---
  --------------------------------------------------------------------------------------------------------

Preencher com resultados reais.

------------------------------------------------------------------------

# 38. Definition of Done do sistema final

O projeto não está "pronto" porque gera respostas convincentes.

Considere a versão final concluída quando:

-   [ ] ingestão é reproduzível;
-   [ ] documentos possuem versionamento;
-   [ ] páginas/seções são preservadas;
-   [ ] tabelas importantes são estruturadas;
-   [ ] conteúdo visual relevante é processado;
-   [ ] retrieval possui benchmark;
-   [ ] hybrid search foi comparado com baseline;
-   [ ] reranking foi avaliado;
-   [ ] regras críticas possuem provenance;
-   [ ] vigência temporal é respeitada;
-   [ ] consultas externas usam tools controladas;
-   [ ] agente possui limites de execução;
-   [ ] conclusão cita evidências;
-   [ ] sistema sabe se abster;
-   [ ] existe verifier;
-   [ ] existe audit trail;
-   [ ] existe human review para decisões de risco;
-   [ ] prompt injection documental foi testado;
-   [ ] métricas de qualidade são registradas;
-   [ ] custo é conhecido;
-   [ ] p95 de latência é conhecido;
-   [ ] testes automatizados existem;
-   [ ] falhas externas são tratadas;
-   [ ] arquitetura está documentada.

------------------------------------------------------------------------

# 39. Ordem resumida de estudo

``` text
01 Python/API/SQL/Git
02 LLM fundamentals
03 Tokens/context/prompting
04 Structured outputs
05 Embeddings
06 Vector search
07 Information Retrieval + BM25
08 Basic RAG
09 RAG evaluation
10 Document parsing
11 Chunking
12 Hybrid retrieval
13 Reranking
14 Query rewriting/decomposition
15 Metadata + temporal retrieval
16 Structured knowledge extraction
17 Rule engines
18 Knowledge graphs
19 Graph-assisted RAG / GraphRAG
20 Tool calling
21 Databases/APIs
22 Agents
23 LangGraph
24 Agentic RAG
25 Multimodal document intelligence
26 Provenance/citations
27 Verification
28 Human-in-the-loop
29 Observability
30 Performance
31 Security
32 Adversarial evaluation
33 Production architecture
34 Fine-tuning quando houver motivo concreto
```

------------------------------------------------------------------------

# 40. Princípios para manter durante todo o estudo

### 1. Baseline antes de sofisticação

Não introduza GraphRAG antes de saber onde o RAG convencional falha.

### 2. Retrieval antes de generation

Se a evidência correta não chega ao modelo, melhorar o prompt
dificilmente resolverá.

### 3. Medir antes de otimizar

Toda melhoria importante precisa de comparação.

### 4. Determinístico quando possível

Não peça ao LLM para fazer o que código tradicional consegue fazer com
maior confiabilidade.

### 5. Evidência acima de eloquência

Uma resposta curta e comprovável é melhor que uma resposta convincente
sem suporte.

### 6. Provenance desde o começo

Não tente adicionar rastreabilidade somente no final.

### 7. Complexidade precisa se pagar

Graph, agentes, múltiplos modelos e pipelines sofisticados precisam
melhorar alguma métrica relevante.

### 8. LLM não deve controlar segurança

Autorização, permissões e validações críticas pertencem ao software.

### 9. Dataset de avaliação é parte do produto

Não é apenas ferramenta de teste.

### 10. Codex é multiplicador

Use-o para implementar mais rápido, mas preserve sua capacidade de
explicar arquitetura, interfaces, métricas e failure modes.

------------------------------------------------------------------------

# 41. Resultado esperado ao concluir

Ao terminar esse percurso, você não deverá apenas saber usar:

``` text
LangChain
LangGraph
Vector DB
GraphRAG
LLM APIs
```

Você deverá conseguir receber um problema e decidir:

``` text
Precisa de RAG?
Qual retrieval?
Precisa de BM25?
Precisa de reranker?
Precisa de grafo?
Precisa de regra estruturada?
Precisa de agente?
Quais tools?
Onde usar LLM?
Onde NÃO usar LLM?
Como avaliar?
Como rastrear evidência?
Como reduzir custo?
Como reduzir latência?
Como impedir comportamento perigoso?
```

Esse é o objetivo real da trilha: passar de **"sei usar ferramentas de
LLM"** para **"sei projetar, medir e evoluir sistemas baseados em
LLM"**.
