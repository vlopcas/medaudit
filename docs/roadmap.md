# Roadmap canônico

Este documento define a ordem vigente de evolução do Medaudit. Ele consolida o
[plano de estudos detalhado](plano_estudos_llm_rag_graph_agentic.md), as lições
dos experimentos já executados e uma revisão externa posterior do currículo.
O [status do plano](study-progress.md) registra o que foi realmente validado; a
[arquitetura atual](architecture.md) descreve somente o que existe no código.

O roadmap não é um calendário. Cada etapa avança por evidência, não por tempo
decorrido, e pode antecipar componentes transversais quando um risco concreto
for encontrado.

## Regras de progressão

Cada mudança relevante segue este ciclo:

```text
teoria → implementação mínima → baseline → experimento controlado
       → avaliação → análise de falhas → decisão → integração
```

- complexidade nova precisa superar ou complementar um baseline mensurável;
- datasets de desenvolvimento e holdout têm funções separadas;
- um holdout aberto nunca vira material de ajuste;
- cálculo, validação, permissões e regras formalizáveis permanecem
  determinísticos;
- conteúdo documental é dado não confiável;
- ausência de evidência, incerteza e revisão humana são estados explícitos;
- dados privados não entram em APIs externas, imagens Docker, logs ou exemplos;
- custo, latência, qualidade e segurança participam da decisão arquitetural.

## Modelo do sistema

O projeto evolui em cinco planos conectados, sem tratá-los como um único
“pipeline de RAG”:

| Plano | Responsabilidade |
|---|---|
| Conhecimento | fontes, ingestão, normalização, versões, chunks e índices |
| Contexto | instruções, consulta, evidências, regras, estado e orçamento |
| Raciocínio | modelo, código determinístico, tools e verificação |
| Controle | roteamento, permissões, limites, retries e encerramento |
| Qualidade | evals, provenance, observabilidade, regressões e revisão humana |

## Sequência principal

### 1. Fundação e governança

Abrange engenharia-base, Docker, testes, documentação, privacidade e contratos
provider-neutral.

Critério de avanço: ambiente reproduzível, dados privados ignorados, módulos
tipados, checks automatizados e decisões documentadas.

Estado: concluído para o ciclo atual.

### 2. Fundamentos de LLM aplicados

Tokens, attention, Transformer, decoding e prompting continuam no plano
original. A extensão necessária é relacionar prefill, decode, KV cache, GQA,
quantização, batching e serving a memória, throughput, TTFT e latência.

Esse estudo pode ocorrer em paralelo e não bloqueia o fluxo principal. Não há
objetivo de treinar um foundation model.

Critério de avanço: explicar as consequências arquiteturais e medi-las em um
experimento local pequeno.

Estado: parcial.

### 3. Knowledge pipeline, IR e RAG básico

Inclui identidade por hash, catálogo, parsing, OCR, chunking, snapshots
temporais, BM25, embeddings, busca híbrida, reranking, abstention, geração
grounded e citações.

O ciclo futuro de Ingestion Engineering complementará a base com idempotência
operacional, deduplicação, retomada, DLQ, reindexação, propagação de remoções e
publicação versionada de índices. Isso será feito quando houver um workload que
permita medir essas propriedades, não como infraestrutura especulativa.

Critério de avanço: lineage documento–chunk–índice–evidência reproduzível e
comparações por eval entre alternativas.

Estado: base implementada; ingestão operacional e estratégias adicionais de
chunking permanecem parciais.

### 4. Query Understanding e Context Engineering

Roteamento explícito, planejamento, execução e agrupamento por passo formam a
base atual. O próximo componente estrutural é um compilador de contexto
provider-neutral, responsável por:

- inventariar cada item e sua origem;
- separar estruturalmente instruções, consulta, evidências, regras e estado;
- aplicar orçamento de tokens e limites por classe;
- ordenar e deduplicar evidências sem perder provenance;
- registrar apenas metadados seguros para auditoria;
- recusar contextos incompletos ou inseguros antes da geração.

O gate experimental baseado somente em expressões regulares foi rejeitado no
holdout. Segurança de contexto deve usar defesa em profundidade; nenhum detector
isolado transforma evidência não confiável em conteúdo seguro.

Critério de avanço: explicar por que cada item entrou no contexto, qual seu
custo, sua origem e qual política o autorizou, com testes de orçamento,
isolamento, posição e conteúdo adversarial.

Estado: o caminho estrutural e a aplicação opt-in foram validados com clientes
falsos. O primeiro benchmark do modelo local pela aplicação preservou 100% de
preparação e validação, mas obteve 25% de acurácia de status e 0% de conteúdo
nos casos respondíveis; a geração local não foi promovida.

### 5. Regras estruturadas e conhecimento temporal

Extrair regras candidatas para schema versionado, validar tipos e vigência e
executar lógica formalizável fora do LLM. O modelo pode auxiliar extração, mas
não decide silenciosamente cobertura, pagamento ou validade normativa.

Critério de avanço: casos temporais, exceções e conflitos são reproduzíveis,
explicáveis e encaminhados para revisão quando necessário.

Estado: temporalidade antecipada parcialmente; motor de regras não iniciado.

### 6. Grafos e primeiro checkpoint arquitetural

Modelar entidades e relações somente depois de definir um slice multi-hop que o
baseline atual não resolve. Comparar retrieval convencional, regras e
graph-assisted retrieval sobre a mesma avaliação.

Critério de avanço: o grafo permanece apenas se trouxer ganho mensurável no
slice-alvo que justifique ETL, modelagem e operação adicionais.

Estado: não iniciado.

### 7. Tools, dados estruturados e agentes

Introduzir primeiro tools estreitas, tipadas, autorizadas e idempotentes para
SQL ou APIs. Comparar workflow determinístico com decisões dinâmicas antes de
adotar agentes ou LangGraph.

Critério de avanço: schemas, least privilege, timeout, orçamento, limite de
passos, prevenção de loops, confirmação para ações sensíveis e terminação
explícita.

Estado: não iniciado.

### 8. Multimodalidade, verifier e human-in-the-loop

Avaliar tabelas, imagens, layout e OCR por slices próprios. Ligar afirmações a
evidências, verificar vigência e extrapolação e encaminhar risco ou ambiguidade
para revisão humana.

Critério de avanço: falhas multimodais são mensuradas separadamente e nenhuma
conclusão de alto impacto é automatizada sem política explícita.

Estado: parsing multimodal básico e provenance parcial foram antecipados;
verifier e workflow humano não foram iniciados.

### 9. Evaluation avançada

Evaluation atravessa todas as fases. A evolução inclui taxonomia e slices,
hard negatives, regressões por falha, graders determinísticos, calibração de
LLM-as-a-judge contra humanos, comparação pareada e gates de CI/release.

Critério de avanço: médias não escondem regressões críticas e cada mudança de
modelo, prompt, parser, chunker, embedding, índice ou workflow dispara a suíte
proporcional ao risco.

Estado: infraestrutura experimental forte; calibração humana, estatística e
gates de release permanecem futuros.

### 10. Production e LLMOps

Somente após um fluxo funcional estável: API, filas, concorrência, retries,
timeouts, circuit breaking, cache, versionamento de artefatos, staging,
canary/shadow, rollback, SLOs, tracing, custos, backup, restore e resposta a
incidentes.

Observabilidade segue o princípio `metadata-rich, content-minimal`: IDs, hashes,
versões, contagens e tempos por padrão; conteúdo somente com autorização e
governança específicas.

Critério de avanço: falhas induzidas degradam de modo previsível e versões de
aplicação, modelo, prompt, dataset, parser e índice podem ser reconstruídas ou
revertidas.

Estado: ambiente local reproduzível existe; operação production-like não foi
iniciada.

### 11. Seleção arquitetural e capstone

Executar a mesma avaliação relevante contra a menor seleção aplicável entre
código determinístico, SQL/tool, long-context, BM25, dense, híbrido, reranking,
regras, grafo e workflow agêntico.

Critério final: escolher a menor arquitetura que atende qualidade, segurança,
latência, custo, privacidade e operação — inclusive quando a resposta correta é
não usar LLM, RAG, grafo ou agente.

## Próximos marcos

1. Diagnosticar em desenvolvimento sintético por que o request compilado induz
   abstention estável no modelo local, comparando-o com a última configuração
   local aprovada sem reutilizar holdout para ajuste. A instrução isolada
   removeu a abstention, mas produziu falha estruturada nas nove tentativas
   respondíveis; o próximo controle acrescenta somente o schema limitado.
2. Formular uma única candidata controlada e avaliá-la primeiro em novos casos
   de desenvolvimento; qualquer holdout posterior deverá ser inédito.
3. Manter síntese desabilitada e o corpus privado bloqueado até qualidade,
   grounding, segurança e repetibilidade passarem juntas.
4. Retomar regras estruturadas e consolidar a temporalidade já antecipada.
5. Executar o primeiro checkpoint de seleção arquitetural antes de grafos.

O detalhamento curricular completo continua no
[plano original](plano_estudos_llm_rag_graph_agentic.md); números e decisões
observados permanecem em [Resultados](results/README.md) e
[ADRs](decisions/ADR-001-private-data-governance.md).
