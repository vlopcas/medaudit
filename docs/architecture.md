# Arquitetura atual

Esta página descreve apenas o que já existe. A arquitetura-alvo mais ampla está
no [plano de estudos](plano_estudos_llm_rag_graph_agentic.md).

## Fluxo documental

```text
user query
    ↓ ExplicitQueryRouter
    ├── requires_external_data → encerra sem ferramenta
    ├── requires_decomposition
    │     ↓ DeterministicQueryPlanner
    │     ├── temporal_snapshots → passos não executados
    │     ├── comparison_scopes → passos não executados
    │     └── needs_clarification → encerra sem passos
    └── direct_retrieval
          ↓ DeterministicQueryAnalyzer
QueryAnalysis
    ├── intent
    ├── reference date and conservative entities
    └── external-data and decomposition signals

source bytes
    ↓ ParserRegistry (media type allowlist)
DocumentParser
    ↓
ParsedDocument
    └── ordered DocumentElement[]
          ├── kind
          ├── page
          ├── section
          └── deterministic element_id
    ↓ Chunker
Chunk[]
    ├── source element_ids
    ├── document version
    └── deterministic chunk_id
    ↓ versioned local serialization
ignored processed artifact
    ↓ retrieval boundary
    ├── BM25Index (baseline principal)
    ├── DenseIndex (experimental)
    ├── ReciprocalRankFusion (experimental)
    └── SemanticCandidateReranker (experimental)
SearchResult[]
    ├──→ evaluation
    │    Hit Rate / Recall / MRR / abstention
    ↓ frozen confidence policy
RetrievalDecision
    ├── insufficient_evidence → encerra sem LLM
    └── accepted evidence
          ↓ structured grounded request
        LLMClient
          └── LlamaCppClient → servidor local isolado
          ↓ deterministic response validation
        answer + traceable citations
```

Os caminhos denso, híbrido e de reranking existem para comparação controlada.
Eles não foram promovidos ao caminho principal porque os experimentos de
calibração ainda não demonstraram ganho suficiente sobre BM25. Da mesma forma,
o adaptador generativo está operacional, mas permanece restrito a dados
sintéticos: o modelo atual não atingiu o critério de conteúdo no holdout
congelado.

O roteamento explícito é uma fronteira determinística integrada por meio do
`RoutedEvidenceFirstPipeline`. Somente `direct_retrieval` alcança o pipeline de
evidências. A rota de decomposição agora contém um plano determinístico para
múltiplas datas ou comparações sintaticamente separáveis; casos ambíguos pedem
esclarecimento. Esses passos ainda não são executados e nenhuma rota habilita
ferramentas externas.

Um `DeterministicDecompositionExecutor` consegue executar os
passos preservando suas fronteiras: comparações usam um pipeline de evidências
por escopo e consultas temporais recebem um pipeline resolvido para cada data.
Se qualquer passo se abstiver, a execução inteira fica como
`insufficient_evidence`. O componente é uma dependência opt-in do fluxo roteado:
sem executor explicitamente configurado, a decisão continua contendo somente o
plano. Ele não combina evidências nem gera respostas.

Um estágio posterior agrupa as evidências executadas sem apagar
as fronteiras dos passos. Cada grupo conserva o passo, seu escopo ou data e as
citações ordenadas originais. Evidência parcial permanece auditável, mas o
pacote só libera uma futura síntese quando todos os passos estiverem `ready`.
Quando o executor opt-in está configurado, esse pacote integra automaticamente
a decisão roteada. Ele ainda não dispara síntese.

Um contrato provider-neutral validado de síntese decomposta transforma pacotes
completos em requests estruturados. A resposta é modelada como afirmações
atômicas, cada uma com suportes que vinculam `step_id` a citações daquele mesmo
grupo. O validador rejeita citações cruzadas e respostas que omitam qualquer
grupo. Um benchmark isolado conecta esse contrato ao cliente LLM somente sobre
evidências sintéticas; o modelo local respondeu corretamente apenas um dos
quatro casos respondíveis na observação inicial. O protocolo repetido confirmou
abstention excessiva e isolou variação de status em um dos cinco casos. Essa
conexão não integra o runtime nem foi promovida para holdout. Uma variante que
explicita quando responder removeu a abstention em uma rodada, mas outra rodada
atingiu o limite de contexto e falhou após cerca de 119 segundos. Ela permanece
somente no benchmark. Um limite opcional de 512 tokens no adaptador reduziu essa
cauda para menos de sete segundos, mas ainda produziu uma tentativa truncada em
30. O schema experimental limitado eliminou truncamentos em duas rodadas e
atingiu 30/30 respostas válidas e corretas. A configuração permanece fora do
runtime e está autorizada somente a avançar para um novo holdout sintético
congelado. Esse holdout passou nos gates agregados, mas falhou de forma
consistente no conteúdo da categoria com instrução não confiável dentro da
evidência. Um diagnóstico separado mostrou recall factual de 100%, mas somente
66,7% de ausência de conceitos proibidos: marcadores falsos de sistema e JSON
embutido contaminaram o conteúdo. A configuração permanece fora do runtime e do
corpus privado. Endurecer o prompt elevou a taxa para 83,3%, mas apenas deslocou
a falha para outro formato. Um gate determinístico e provider-neutral foi então
implementado como componente isolado. No desenvolvimento sintético balanceado,
ele atingiu 100% de recall em seis ataques e 100% de especificidade em seis
textos legítimos semelhantes, retornando somente IDs e códigos de sinal. O gate
continua fora do runtime até passar por holdout inédito; sua função é colocar
evidência suspeita em revisão, não modificar ou tornar seguro seu conteúdo. No
holdout inédito, porém, seu recall de ataques caiu para 50% e sua especificidade
para 87,5%. O gate foi rejeitado para integração e permanece apenas como
experimento; enumerar expressões regulares não constitui uma fronteira de
segurança generalizável.

Um compilador de contexto provider-neutral existe como componente isolado e
ainda não participa do runtime. Ele mantém instrução, consulta e evidências em
itens tipados, aplica um orçamento determinístico, conserva provenance por
passo e registra exclusões sem duplicar o texto rejeitado. Evidências continuam
marcadas como dados não confiáveis; somente a instrução pertence ao plano de
controle. Orçamento que elimine um passo, identidade conflitante ou ID marcado
para revisão bloqueiam geração antes de qualquer renderização para um provider.
No conjunto sintético de desenvolvimento, o contrato atingiu 100% nos seis
casos de seleção, budget, revisão, deduplicação e evidência insuficiente. Isso o
autoriza somente a enfrentar um holdout inédito; a integração continua
bloqueada. O holdout posterior atingiu 100% nos oito casos inéditos, incluindo
budgets limítrofes, colisões e precedência de recusas. O contrato está aprovado
para uma integração opt-in à síntese decomposta; o modelo local e o corpus
privado continuam bloqueados.

Um renderer opt-in transforma apenas um `CompiledContext` em estado `ready` no
mesmo `LLMRequest` decomposto já validado. Antes da renderização, ele revalida o
budget contabilizado, unicidade dos IDs, fronteiras de confiança e vínculos de
cada evidência aos passos. Testes comprovam equivalência exata com o construtor
anterior e recusam contextos bloqueados ou adulterados. O caminho padrão do
runtime ainda não usa esse renderer e nenhuma chamada adicional de LLM foi
habilitada.
Uma avaliação adversarial separada aceitou o controle íntegro e recusou as doze
mutações de status, budget, identidade, confiança e provenance, atingindo 13/13
casos. A fronteira está autorizada apenas a avançar para holdout estrutural
inédito e continua opt-in. Nesse holdout, porém, a correspondência exata caiu
para 25% e somente 2/7 mutações inseguras foram recusadas. Alterações de conteúdo
pós-compilação, membership adicional e inversão de grupos atravessaram a
fronteira. O renderer foi rejeitado para runtime; a próxima candidata deve usar
representação canônica selada e invariantes completas de topologia. Essa
candidata agora anexa um SHA-256 determinístico que cobre todos os campos do
contexto e é recalculado pelo renderer. Unicidade por grupo e correspondência
bidirecional entre grupos e memberships continuam sendo validadas como regras
semânticas. O digest não é autenticação contra execução de código e a candidata
ainda não foi promovida nem integrada ao runtime. No desenvolvimento sintético,
ela acertou 21/21 casos e recusou 20/20 mutações. O próximo limite é um novo
holdout estrutural congelado, não a ativação do caminho padrão. A primeira
tentativa desse holdout ficou inconclusiva: nove mutações efetivas foram
recusadas, mas três transformações eram no-ops porque o adaptador não preservava
os campos desafiados. A arquitetura não foi promovida; o harness deve validar
que cada mutação realmente altera o objeto antes de uma nova avaliação.
O avaliador agora aborta diante de mutação nula, e o adaptador preserva página e
seção quando declaradas. Essas mudanças corrigem o instrumento, sem promover o
renderer ou reinterpretar o holdout já executado. O harness corrigido atingiu
7/7 no desenvolvimento, cobrindo os campos antes descartados. Ele pode agora
ser usado para um novo holdout congelado.
O segundo holdout atingiu 11/11, recusando dez mutações inéditas e efetivas. A
fronteira selada está aprovada para ser conectada ao pipeline por um caminho
experimental explicitamente opt-in e com falha fechada. Essa decisão não
promove a síntese local, não libera o corpus privado e não altera o runtime
padrão.

O `CompiledContextGateway` materializa essa integração como componente isolado.
Seu modo padrão `disabled` não compila nem produz request. O modo
`experimental` recebe um pacote agrupado, compila o contexto, exige estado
`ready`, verifica o selo e só então produz o `LLMRequest`. Falhas esperadas
retornam sem request e com códigos genéricos. A telemetria registra apenas
estado, contagens, tokens, budget e duração; o componente não possui cliente de
LLM e ainda não é chamado pelo `RoutedEvidenceFirstPipeline`.
Em desenvolvimento sintético, o gateway atingiu 5/5 tanto na correspondência
esperada quanto na regra request-presente-se-e-somente-se-`prepared`. Ele segue
fora do roteador até passar por holdout inédito. O holdout posterior atingiu
5/5 nas duas métricas, incluindo curto-circuito desabilitado, bundle incompleto,
revisões e deduplicação compartilhada. Isso autoriza somente a injeção opcional
do gateway no roteador, mantendo o padrão desabilitado e sem chamada de modelo.
O roteador agora oferece `retrieve_with_compiled_request` como operação
separada. Ela reutiliza `retrieve` e só encaminha um bundle de decomposição já
executado ao gateway injetado. Sem bundle, retorna apenas a decisão roteada; com
o gateway padrão, retorna telemetria `disabled` e nenhum request. O método
original e todas as demais rotas permanecem inalterados.
A avaliação integrada atingiu 7/7 em correspondência e presença segura de
request, cobrindo rotas direta e externa, ausência de executor, modo
desabilitado, preparação válida, evidência insuficiente e revisão. A unidade
continua experimental. No holdout inédito, preservou 6/6 na segurança de
emissão, porém atingiu apenas 5/6 na correspondência: uma dependência externa
formulada pela composição de origem e atualidade seguiu para recuperação
direta. A promoção foi rejeitada; o holdout permanece congelado e a correção
deve ocorrer em desenvolvimento separado antes de nova avaliação inédita. A
nova candidata trata formulações genéricas como dependência externa somente
quando ação de consulta, origem externa e atualidade aparecem juntas. Ela
atingiu 10/10 no desenvolvimento integrado, com controles negativos para
menções documentais. O segundo holdout integrado também atingiu 10/10 em
correspondência e segurança de emissão, cobrindo seis categorias inéditas. A
fronteira estrutural está aprovada apenas para receber uma camada de
orquestração experimental, injetável e desabilitada por padrão; modelo local e
corpus privado continuam fora desse caminho.

`GroundedSynthesisOrchestrator` implementa essa próxima fronteira sem ser
ativado automaticamente pelo pipeline. Ele exige request preparado, chama um
`LLMClient` injetado somente em modo experimental e mantém a resposta bruta
interna até a validação contra o bundle original. Somente uma resposta
decomposta validada é liberada; falhas do cliente ou do contrato terminam sem
resposta e com código genérico. Em desenvolvimento com clientes falsos, os sete
fluxos atingiram 100% em correspondência e segurança de liberação. O holdout
posterior também atingiu 100% nos nove casos inéditos, cobrindo bloqueios,
suporte combinado, respostas inválidas e timeout. Isso autoriza somente uma
composição de aplicação opt-in que preserve as APIs atuais; nenhum modelo foi
promovido e o caminho padrão permanece sem síntese.

`GroundedSynthesisApplication` compõe o pipeline e o orquestrador sem duplicar
suas políticas. A operação preserva lado a lado o resultado roteado e a síntese
e usa um orquestrador desabilitado por padrão. Em desenvolvimento sintético,
atingiu 6/6 em correspondência, segurança de invocação e segurança de
liberação. Ela ainda não é um endpoint e precisa de holdout inédito antes de
qualquer conexão adicional. O holdout posterior atingiu 9/9 em correspondência,
segurança de invocação e segurança de liberação. A composição está aprovada
como arquitetura experimental com cliente falso, não como prova de qualidade
do modelo. O caminho padrão continua desabilitado e o corpus privado permanece
fora de escopo. No benchmark posterior com `Qwen3-4B Q4_K_M`, a aplicação
preparou, invocou e validou 12/12 execuções, mas o modelo se absteve nas nove
tentativas respondíveis. A acurácia de status foi 25% e a de conteúdo, 0%.
Assim, a arquitetura preservou seus limites de segurança, mas o modelo e o
request atual não foram aprovados para uso.

Uma política de instrução explícita pode ser selecionada antes da compilação e
passa a fazer parte do contexto selado. Ela é opt-in e não muda input, schema,
temperatura nem o padrão do gateway. Isoladamente, porém, produziu nove falhas
fechadas do cliente nas nove tentativas respondíveis e foi rejeitada. Nenhuma
resposta inválida atravessou o orquestrador.

O gateway também aceita uma política de schema opt-in que limita claims,
textos, suportes e citações. Com a instrução explícita, teto de 512 tokens e
esses limites, o modelo atingiu 12/12 em validação e status e 9/9 em conteúdo
respondível no desenvolvimento, com estabilidade exata. A configuração está
apta somente a um holdout sintético novo; o padrão continua baseline e
desabilitado. Esse holdout preservou 18/18 saídas estruturalmente válidas, mas
caiu para 66,7% em status e 75% em conteúdo respondível. Instrução não
confiável e evidência insuficiente continuam sem proteção semântica adequada.
A configuração foi rejeitada e não altera o caminho padrão.

`GroundedAnswerVerifier` é uma fronteira independente e opcional entre a
validação grounded e a liberação. Ela pode liberar, rejeitar ou segurar para
revisão; códigos são fechados e não carregam conteúdo. Rejeição, revisão ou
falha jamais expõem a resposta, e uma saída estruturalmente inválida nem chega
ao verificador. O contrato atingiu 7/7 fluxos e 100% de segurança de liberação
com verificadores falsos. Ainda não existe uma estratégia semântica promovida.

`ConservativeLexicalVerifier` é a primeira estratégia experimental dessa
fronteira. Ele compara tokens do claim somente com evidências citadas e envia
instruções explícitas para revisão. No desenvolvimento, liberou todos os casos
seguros, mas bloqueou apenas um de três inseguros: expansão sem suporte e
contradição pontual atravessaram a verificação. A estratégia foi rejeitada e
não integra o caminho aprovado.

`StructuredFactVerifier` é a candidata determinística seguinte. Ele reconhece
somente quantidades com unidade, códigos alfanuméricos e polaridade de
permissão ou proibição nas evidências citadas. Divergências são rejeitadas;
claims sem um tipo reconhecido e evidência suspeita seguem para revisão. No
desenvolvimento sintético atingiu 10/10 e repetiu 10/10 em holdout congelado.
Está aprovado somente como componente experimental opt-in e não integra o
caminho padrão.
Quando injetado no `GroundedSynthesisOrchestrator`, o verificador também
atravessou a composição completa da aplicação em 7/7 fluxos de desenvolvimento
e 100% de segurança de liberação. O opt-in desligado preserva o comportamento
anterior; rejeição e revisão nunca carregam a resposta para fora do
orquestrador. Em holdout próprio e congelado, repetiu 9/9 e 100% de segurança
de liberação. Continua opt-in, experimental e fora do caminho padrão.
Com o modelo local, porém, essa integração reteve seis de doze saídas de um
controle que já tinha 100% de conteúdo e segurança. Quantidade e código foram
falsamente retidos de forma estável; a composição local foi rejeitada e não
integra o caminho aprovado.

Uma variante experimental preserva extrações determinísticas e usa o
`LlamaCppClient` apenas para os três campos semânticos, mas foi rejeitada no
desenvolvimento e não pertence ao fluxo principal.
Uma política anterior em camadas combinava sinais determinísticos e semânticos;
ela permanece apenas como experimento e não controla o pipeline.

## Regras estruturadas

`DeterministicRuleEngine` resolve apenas regras já estruturadas e revisadas.
Cada versão declara escopo, decisão `allow` ou `deny`, vigência inclusiva,
prioridade, condições exatas e documento de origem. A maior prioridade
aplicável vence; decisões divergentes na mesma prioridade produzem `review`, e
ausência de regra produz `no_match`. Toda decisão aplicada conserva provenance
em `rule_id@version`.

Esse motor é independente do RAG e do LLM. Não existe importação do catálogo
privado nem extração automática aprovada.

Uma heurística estrutural para decomposição também existe como experimento
isolado. Ela foi rejeitada no holdout e não é chamada pelo analisador nem pelo
roteador principal.

Em paralelo, o inventário técnico alimenta um catálogo privado revisado. O hash
define identidade; metadados semânticos e temporais só se tornam confiáveis
após revisão humana no documento de origem.
Um gate entre catálogo e ingestão valida revisão, vigência e integridade do
conteúdo antes de permitir parsing e chunking.
O processamento materializa JSONL privado por data de referência. Cada registro
preserva o identificador e a versão do documento, período de vigência,
localização estrutural e IDs dos elementos que originaram o chunk.
O roteador de chunking mantém páginas e seções para documentos estruturais e
agrupa linhas consecutivas por aba para planilhas, repetindo o cabeçalho e
registrando o intervalo de linhas.

## Limites dos módulos

- `documents`: modelos de domínio sem dependência de formato ou fornecedor;
- `parsing`: adaptadores que convertem bytes em elementos normalizados;
- `chunking`: estratégias intercambiáveis sobre a representação normalizada;
- `retrieval`: índices e resultados de busca;
- `evaluation`: datasets, métricas e execução de benchmarks;
- `rag`: gate de abstention, pacote de evidências, prompt e validação de citações;
  inclui também compilação selada e gateway integrado somente por caminho
  experimental e opt-in;
- `llm`: contrato independente de fornecedor e adaptador HTTP restrito a um
  servidor `llama.cpp` local;
- `ingestion`: inventário, seleção de parser, pipeline local e serialização.
- `catalog`: identidade, metadados temporais e relações de substituição.

Os parsers atuais aceitam texto UTF-8, PDF textual, XLSX e XLS. PDF preserva
página e bounding box; planilhas preservam aba e linha. O chunker inicial usa
caracteres, respeita páginas e seções e mantém tabelas e figuras isoladas.

OCR é um caminho local e opt-in. O fallback preserva a extração nativa e aciona
o provedor somente nas páginas sem texto, marcando os elementos resultantes com
o método utilizado. Não existe fallback implícito para APIs externas.

O registro de parsers falha para tipos desconhecidos ou ambíguos. O pipeline
não acessa rede nem armazenamento: recebe bytes e retorna um resultado. A
persistência é uma responsabilidade separada e seus artefatos devem permanecer
em `data/processed/`, que é ignorado pelo Git.

## Regras estruturadas revisadas

O módulo `medaudit.rules` mantém a execução de regras fora do caminho
generativo. O motor resolve regras tipadas por escopo, data, condições e
prioridade; ausência de regra e conflitos permanecem estados explícitos. Uma
auditoria estática independente compara pares de mesma prioridade e escopo,
considerando vigências sobrepostas e condições que possam coexistir. Decisões
divergentes são classificadas como conflito e decisões iguais como
redundância.

Essa análise é conservadora e limitada à linguagem atual de condições exatas.
Ela não publica regras, não interpreta documentos e não toca o catálogo
privado. O gate de admissão bloqueia qualquer conflito, encaminha redundâncias
não revisadas para revisão e rejeita referências de revisão que não correspondam
a um achado atual. Somente catálogos sem pendências chegam ao motor.
Essa composição repetiu o comportamento esperado em holdout sintético congelado
e permanece isolada de qualquer catálogo privado ou fluxo real de publicação.

A fronteira experimental seguinte recalcula a admissão antes de criar um
`PublishedRuleCatalog`. O snapshot ordena as regras e recebe um SHA-256
determinístico derivado de todo o conteúdo estruturado. Identidade, versão e
origem permanecem no catálogo. Reescrever uma versão existente ou introduzir
uma versão não monotônica é bloqueado; uma versão nova requer revisão explícita
do par substituído/substituto. Remoções ainda param em revisão, sem caminho de
aprovação nesta primeira iteração. O incremento posterior aceita aposentadorias
somente quando todas as versões removidas são declaradas e a revisão referencia
o `publication_id` do snapshot anterior. Aprovações parciais mantêm o catálogo
em revisão; referências antigas ou destinadas a regras presentes são recusadas.
A composição completa repetiu o comportamento esperado em holdout sintético
congelado. Persistência e integração com catálogo privado continuam ausentes.
O [checkpoint entre regras e grafo](architecture-checkpoints/001-phase-9-rules-to-graph.md)
adiou Graph RAG até que um benchmark demonstre uma lacuna multi-hop real.
O primeiro benchmark encontrou quatro lacunas candidatas e autorizou somente um
protótipo de traversal em memória, com IDs exatos, relações revisadas, limite de
quatro saltos e provenance por aresta. Nenhum banco de grafo foi adotado.
O protótipo recuperou as quatro categorias no desenvolvimento sintético. Ele
permanece isolado porque recebe IDs já resolvidos; a ligação entre pergunta,
entidades e traversal ainda precisa de avaliação própria antes de integrar o
retrieval.
Essa ligação agora possui uma primeira fronteira determinística: somente
perguntas com intenção de caminho e duas referências revisadas geram uma
solicitação tipada. Casos incompletos ou ambíguos param em revisão. A composição
com traversal e a comparação no mesmo input do baseline continuam pendentes.

## Decisões relacionadas

- [ADR-001: governança dos dados privados](decisions/ADR-001-private-data-governance.md)
- [ADR-002: separação entre parsing e chunking](decisions/ADR-002-parsing-chunking-boundary.md)
- [ADR-003: adaptadores locais para PDF, XLSX e XLS](decisions/ADR-003-local-document-parsers.md)
- [ADR-004: OCR local explícito](decisions/ADR-004-explicit-local-ocr.md)
- [ADR-005: desenvolvimento em Docker](decisions/ADR-005-containerized-development.md)
- [ADR-006: catálogo documental privado](decisions/ADR-006-private-document-catalog.md)
- [ADR-007: materialização temporal de chunks privados](decisions/ADR-007-temporal-private-chunk-materialization.md)
- [ADR-008: avaliação privada de retrieval](decisions/ADR-008-private-retrieval-evaluation.md)
- [ADR-009: busca híbrida independente de fornecedor](decisions/ADR-009-provider-neutral-hybrid-retrieval.md)
- [ADR-010: embeddings multilíngues locais](decisions/ADR-010-local-multilingual-embeddings.md)
- [ADR-011: geração condicionada a evidências rastreáveis](decisions/ADR-011-gated-evidence-first-generation.md)
- [ADR-012: geração estruturada com modelo local](decisions/ADR-012-local-structured-generation.md)
- [ADR-013: baseline determinístico de Query Understanding](decisions/ADR-013-deterministic-query-understanding-baseline.md)
- [ADR-014: roteamento explícito antes do retrieval](decisions/ADR-014-explicit-pre-retrieval-routing.md)
- [ADR-015: planos determinísticos de decomposição](decisions/ADR-015-deterministic-decomposition-plans.md)
- [ADR-016: execução opt-in de planos de decomposição](decisions/ADR-016-opt-in-decomposition-execution.md)
- [ADR-017: pacotes de evidências preservam o escopo dos passos](decisions/ADR-017-step-scoped-evidence-bundles.md)
- [ADR-018: geração decomposta usa afirmações com suporte por passo](decisions/ADR-018-claim-scoped-decomposed-generation.md)
- [ADR-019: compilação de contexto é uma fronteira explícita](decisions/ADR-019-explicit-context-compilation-boundary.md)
- [ADR-020: gateway opt-in para contexto compilado](decisions/ADR-020-opt-in-compiled-context-gateway.md)
- [ADR-021: orquestração de síntese com liberação validada](decisions/ADR-021-guarded-synthesis-orchestration.md)
- [ADR-022: aplicação de síntese opt-in](decisions/ADR-022-opt-in-synthesis-application.md)
- [ADR-023: verificação independente antes da liberação](decisions/ADR-023-independent-release-verification.md)
- [ADR-024: regras estruturadas revisadas](decisions/ADR-024-reviewed-structured-rule-engine.md)
- [ADR-025: publicação versionada de regras](decisions/ADR-025-versioned-rule-publication.md)
- [ADR-026: grafo adiado até lacuna medida](decisions/ADR-026-defer-graph-until-measured-gap.md)
- [ADR-027: traversal em grafo limitado e revisado](decisions/ADR-027-bounded-reviewed-graph-traversal.md)

## Ambiente de execução

Docker Compose é a referência reproduzível. A imagem contém Python e OCR, mas
não contém o corpus privado. Serviços que processam o corpus executam sem acesso
à rede, com filesystem raiz somente leitura e sem capabilities adicionais. O
corpus entra apenas por bind mount somente leitura; artefatos locais saem por um
mount separado e ignorado.

Os serviços de download de modelos são exceções explícitas: possuem acesso à
internet, não montam `data/` e gravam somente em `models/`. Durante os benchmarks
generativos, cliente e servidor comunicam-se por uma rede interna do Docker sem
publicar a porta do modelo no host; tanto o corpus privado quanto APIs externas
permanecem fora desse fluxo.
