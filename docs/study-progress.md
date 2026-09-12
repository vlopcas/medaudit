# Status do plano de estudos

Esta página registra o progresso observado no
[plano de estudos](plano_estudos_llm_rag_graph_agentic.md). O plano continua
sendo o roteiro conceitual; este documento informa o que foi implementado e
validado no repositório.

Os status não significam que um tema deixou de ser estudado. **Concluída**
indica que o critério atual para avançar foi atendido; **parcial** indica uma
base utilizável com trabalho previsto; **experimental** identifica uma hipótese
implementada, mas ainda não promovida; e **não iniciada** indica ausência de uma
implementação dedicada.

## Visão atual

| Fase | Tema | Status | Evidência no projeto |
|---|---|---|---|
| 0 | Preparação | Concluída | Estrutura, qualidade, Docker, governança de dados e documentação versionada. |
| 1 | Fundamentos de LLMs | Parcial | Inferência local estruturada e prompting foram exercitados; o modelo atual não passou no holdout. |
| 2 | Embeddings e Information Retrieval | Concluída para o ciclo atual | BM25, embeddings locais, busca densa e métricas reproduzíveis foram implementados e comparados. |
| 3 | Primeiro RAG | Concluída tecnicamente | Retrieval, gate, prompt, geração local e citações formam um pipeline ponta a ponta sobre dados sintéticos. |
| 4 | Evaluation desde cedo | Em andamento contínuo | Golden sets, split, calibração, holdout, diagnósticos e métricas de retrieval e geração estão presentes. |
| 5 | Document parsing e chunking | Parcial | Texto, PDF, XLS/XLSX, OCR por página e chunking estrutural estão implementados; novas estratégias ainda podem ser comparadas. |
| 6 | Hybrid Retrieval | Experimental, não promovida | BM25, dense e RRF foram comparados; BM25 permanece como baseline principal. |
| 7 | Reranking | Experimental, não promovida | Reranking semântico restrito aos candidatos foi avaliado sem justificar promoção. |
| 8 | Query Understanding | Próxima fase | Ainda não há módulo dedicado de classificação, reescrita, decomposição ou roteamento de consultas. |
| 9 | Regras estruturadas | Não iniciada | Será tratada depois do ciclo de Query Understanding. |
| 10 | Temporalidade e versionamento | Parcial, antecipada | Catálogo temporal, relações de substituição, snapshots por data e avaliações temporais já existem. |
| 11–18 | Grafos, tools, APIs e agentes | Não iniciadas | Permanecem no roteiro futuro. |
| 19 | Provenance e citações | Parcial, antecipada | IDs determinísticos, origem dos chunks e validação das citações já atravessam o pipeline. |
| 20–26 | Verifier até arquitetura final | Não iniciadas | Permanecem no roteiro futuro. |

## Decisões vigentes

- BM25 continua sendo o baseline de retrieval.
- Dense, RRF e reranking permanecem disponíveis somente como caminhos
  experimentais.
- A política de confiança e abstention é determinística e foi congelada antes
  da avaliação final.
- O pipeline generativo aceita somente evidências liberadas pelo gate e valida
  as citações contra o contexto fornecido.
- O modelo local atual não está autorizado a processar o corpus privado: no
  holdout sintético, produziu respostas completas em 3 de 7 casos respondíveis.
- Documentos, extrações, metadados e artefatos do corpus real continuam privados
  e ignorados pelo Git.

## Próximo marco

O próximo ciclo é a **Fase 8 — Query Understanding**. Antes de implementá-la,
devem ser definidos um contrato pequeno e casos sintéticos para medir pelo
menos classificação da intenção, normalização da consulta e necessidade de
decomposição, sem usar o holdout generativo já aberto como conjunto de ajuste.

Os números e decisões dos experimentos generativos estão em
[Resultados](results/README.md). A composição técnica vigente está em
[Arquitetura atual](architecture.md).
