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
| 8 | Query Understanding | Parcial | Roteamento, planejamento e execução opt-in por passo foram validados; combinação de evidências e reescrita semântica ainda não foram implementadas. |
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

A **Fase 8 — Query Understanding** está em andamento. Após chegar a 100% no
conjunto de desenvolvimento, o baseline determinístico obteve apenas 66,7% no
holdout sintético congelado e não controla o retriever. O próximo ciclo deve
formular outra abordagem usando novos casos de desenvolvimento; o holdout já
aberto não será usado para ajustar regras ou escolher termos.

Uma segunda hipótese manteve datas e códigos determinísticos e delegou três
campos semânticos ao LLM local. Ela atingiu somente 56,25% no próprio conjunto
de desenvolvimento e foi rejeitada sem consumir um novo holdout. O próximo
experimento separou bloqueios conservadores do planejamento e alcançou 87,5%
de rotas corretas, sem bloqueios externos indevidos. A candidata ainda não foi
promovida porque perdeu dois casos de decomposição multi-documento.

A tentativa seguinte de detectar estrutura multi-documento atingiu 100% no
desenvolvimento, mas caiu para 62,5% no holdout e gerou 37,5% de falsos
positivos. Ela foi retirada do analisador principal e preservada apenas como
experimento. O próximo marco deve restringir planejamento automático aos sinais
explícitos já sustentados pelas avaliações.

A política restrita seguinte atingiu 100% em 18 casos de desenvolvimento e 15
casos de holdout. Ela foi promovida antes do retrieval: somente comparação
explícita, múltiplas datas e dependência externa recebem rotas especiais. As
demais formulações seguem diretamente para busca.

O planejador determinístico subsequente atingiu 100% em 12 casos de
desenvolvimento e 12 casos de holdout. Ele materializa passos temporais ou dois
escopos comparáveis somente quando a estrutura é inequívoca; caso contrário,
pede esclarecimento. Os passos estão integrados à decisão roteada, mas ainda
não são executados. O próximo marco é avaliar a recuperação de cada passo e a
combinação de evidências antes de autorizar síntese comparativa.

O executor subsequente atingiu 100% em 12 casos de desenvolvimento e 10 casos
de holdout, incluindo 17 acertos de documento por passo e nove acertos
temporais. Ele foi integrado de forma opt-in: sem resolvedor explícito de
snapshots, o runtime não executa o plano. O próximo marco é definir e avaliar a
combinação determinística das evidências antes de qualquer síntese generativa.

O agrupamento subsequente atingiu 100% em seis casos de desenvolvimento e quatro
casos de holdout, preservando contexto e citações nos sete grupos inéditos.
Evidência parcial continua visível para auditoria, mas bloqueia geração. O
pacote foi integrado ao caminho opt-in; o próximo marco é definir e avaliar o
contrato de síntese comparativa grounded.

O contrato dessa síntese constrói requests agrupados e valida
afirmações atômicas com suporte por `step_id`. Citações de outro grupo, omissão
de um lado e pacotes parciais são rejeitados deterministicamente. Ele atingiu
100% em 12 casos de desenvolvimento e oito casos de holdout, mas ainda não
chamava o modelo local. O benchmark de desenvolvimento seguinte mostrou 100%
de conformidade estrutural, mas o `Qwen3-4B Q4_K_M` respondeu corretamente
somente um dos quatro casos respondíveis e mostrou variação entre execuções.
Três repetições por caso confirmaram 100% de estrutura, somente 33,3% de status
correto, 16,7% de conteúdo correto e estabilidade exata em quatro dos cinco
casos. A integração e o holdout permanecem bloqueados; o próximo marco é testar
uma única alteração controlada. A variante que explicita a decisão entre
resposta e abstention atingiu 100% em 15 tentativas numa rodada, mas uma rodada
anterior teve uma saída inválida de aproximadamente 119 segundos ao alcançar o
limite de contexto. A melhora de qualidade é candidata, não promovida. O próximo
marco limitou a saída a 512 tokens: a pior latência caiu de aproximadamente 119
para 6,88 segundos, mas uma das 30 tentativas ainda foi truncada e inválida. O
holdout continua fechado. O próximo ciclo restringirá somente a forma do JSON
para impedir expansão descontrolada e repetirá o desenvolvimento. O schema
limitado seguinte atingiu 30/30 tentativas estruturadas, grounded e corretas em
duas rodadas, com pior latência de 4,71 segundos. A configuração está elegível
para um novo holdout sintético congelado, mas continua fora do runtime. O
holdout atingiu 100% em estrutura, grounding e status, e 80% em conteúdo, porém
falhou nas três repetições do caso adversarial com instrução não confiável na
evidência. O próximo ciclo é um diagnóstico sintético de segurança separado; o
holdout não será usado para ajuste. O diagnóstico separado obteve 100% de recall
dos fatos, mas só 66,7% de ausência dos conceitos proibidos, com falhas estáveis
em marcadores falsos de sistema e JSON embutido. O próximo ciclo testará uma
única instrução explícita contra repetição de comandos encontrados na evidência.
Ela elevou a ausência de conceitos proibidos para 83,3%, mas deslocou a falha
para overrides em inglês nas seis tentativas de duas rodadas. A mitigação por
prompt foi rejeitada. O próximo marco é um gate determinístico de evidência
suspeita, avaliado também contra falsos positivos legítimos. Esse gate isolado
atingiu 100% de recall nos seis ataques e 100% de especificidade nos seis casos
legítimos semelhantes do conjunto de desenvolvimento. Ele retorna somente IDs
e códigos de sinal, permanece fora do runtime e agora deve enfrentar um holdout
sintético inédito com paráfrases e casos limítrofes adicionais.

Os números e decisões dos experimentos generativos estão em
[Resultados](results/README.md). A composição técnica vigente está em
[Arquitetura atual](architecture.md).
