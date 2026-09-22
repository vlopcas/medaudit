# Status do plano de estudos

Esta página registra o progresso observado no
[roadmap canônico](roadmap.md). O
[plano de estudos detalhado](plano_estudos_llm_rag_graph_agentic.md) conserva o
conteúdo curricular; este documento informa o que foi implementado e validado
no repositório.

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
| 8 | Query Understanding | Concluída para o ciclo atual | Roteamento, planejamento, execução e agrupamento opt-in por passo foram validados; reescrita semântica foi rejeitada. |
| 9 | Regras estruturadas | Concluída para o ciclo sintético | Motor, auditoria, admissão e publicação versionada passaram em desenvolvimento e holdouts controlados. |
| 10 | Temporalidade e versionamento | Parcial, antecipada | Catálogo temporal, relações de substituição, snapshots por data e avaliações temporais já existem. |
| 11–18 | Grafos, tools, APIs e agentes | Traversal de grafo experimental; demais não iniciadas | O protótipo resolveu quatro lacunas sintéticas com IDs já resolvidos; integração e Graph RAG não estão autorizados. |
| 19 | Provenance e citações | Parcial, antecipada | IDs determinísticos, origem dos chunks e validação das citações já atravessam o pipeline. |
| 20–26 | Verifier até arquitetura final | Parcial, experimental | A fronteira foi integrada; a candidata estruturada passou em desenvolvimento e holdout como opt-in estreito. Arquitetura final permanece futura. |

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

O ciclo sintético da **Fase 9 — Regras estruturadas** foi concluído. O motor determinístico
e a auditoria estática passaram em desenvolvimento sintético. A fronteira de
admissão também passou em 5/5 casos: conflito bloqueia, redundância pendente vai
para revisão, redundância explicitamente revisada pode ser admitida e referências
desatualizadas são recusadas. O holdout congelado atingiu 6/6 e está encerrado.
A primeira fronteira sintética de publicação atingiu 9/9, preservou snapshots
determinísticos e bloqueou mutações e substituições não revisadas. O próximo
incremento vinculou aposentadorias ao snapshot anterior e elevou o conjunto para
11/11. O holdout sintético inédito da composição atingiu 8/8 e está encerrado.
O checkpoint arquitetural concluiu que ainda não existe evidência para Graph
RAG. O benchmark seguinte encontrou quatro lacunas candidatas após executar os
baselines atuais. O protótipo determinístico subsequente recuperou as quatro
categorias, preservou provenance e falhou fechado nos controles. Como recebeu
IDs já resolvidos, o próximo marco é avaliar a fronteira entre referência
explícita e solicitação de traversal, sem conexão ao catálogo privado.

O histórico que levou a esse marco permanece abaixo. Na **Fase 8 — Query
Understanding**, após chegar a 100% no
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
sintético inédito com paráfrases e casos limítrofes adicionais. Nesse holdout,
o recall caiu para 50%, a especificidade para 87,5% e a acurácia de quarentena
para 68,75%. A integração foi rejeitada. O conjunto congelado não será usado
para ajustar expressões; uma nova candidata deverá partir de defesa em
profundidade e enfrentar outro holdout inédito. O primeiro componente dessa
nova arquitetura é um compilador de contexto isolado: instrução, consulta e
evidências têm tipos e níveis de confiança distintos; orçamento, deduplicação,
provenance, conflito de identidade e revisão produzem decisões explícitas antes
de qualquer modelo. O próximo marco é avaliar esse contrato em um dataset
sintético de desenvolvimento, ainda sem integrá-lo ao runtime. A avaliação
atingiu 100% nos seis casos e em todas as categorias, incluindo seleção exata,
provenance, exclusões e confiança estrutural. O próximo marco é congelar um
holdout inédito com budgets limítrofes, conflitos e combinações de políticas;
o runtime permanece inalterado. Esse holdout atingiu 100% nos oito casos e em
todas as categorias. O contrato pode agora ganhar um renderer opt-in para
`LLMRequest`, com equivalência estrutural testada e geração condicionada a
`can_generate`; isso não promove o modelo local nem libera o corpus privado. O
renderer opt-in foi implementado e produz request idêntico ao construtor
anterior quando o contexto está completo. Budget inconsistente, confiança
adulterada, grupo vazio ou referência ausente são recusados. O próximo marco é
avaliar essa fronteira de integração em casos sintéticos adversariais antes de
qualquer adoção pelo runtime.
Essa avaliação adversarial atingiu 100% nos 13 casos: o controle íntegro foi
aceito e as doze mutações inseguras foram recusadas. O próximo marco é congelar
um holdout estrutural inédito; compilador, renderer e modelo continuam fora do
caminho padrão e do corpus privado.
O holdout estrutural seguinte reprovou essa fronteira: apenas 25% de
correspondência exata e 28,57% de rejeição das sete mutações inseguras.
Alterações pós-compilação em conteúdo, membership adicional e ordem de grupos
foram aceitas. O renderer não será ativado. O próximo ciclo deve formular um
contexto canônico selado por digest e só depois enfrentar outro holdout. A nova
candidata já serializa deterministicamente estado, budget, itens, ordem,
confiança, provenance, grupos e exclusões e sela o resultado com SHA-256. O
renderer recusa divergências antes de consumir os campos e mantém invariantes
completas de topologia. Esse selo detecta alteração interna, mas não autentica
um contexto contra quem possa recalcular o digest. O próximo marco é um dataset
adversarial sintético de desenvolvimento; runtime, modelo e corpus privado
continuam fora de escopo. Esse desenvolvimento atingiu 100% nos 21 casos e em
todas as onze categorias, recusando as vinte mutações e aceitando o controle.
A candidata está autorizada somente a enfrentar um novo holdout sintético
congelado; nenhuma integração ao runtime foi liberada. A primeira tentativa
recusou 9/9 alterações efetivas, porém três dos doze casos rotulados como
mutações eram no-ops causados pelo adaptador do benchmark. O resultado foi
classificado como inconclusivo. O próximo marco é adicionar uma pré-condição
que rejeite mutações nulas, preservar os campos sob teste e só então congelar
outro holdout; o conjunto comprometido não será ajustado nem reexecutado.
A pré-condição e a preservação opcional de página e seção já foram implementadas
e cobertas por testes. O próximo marco imediato é validar o harness corrigido em
desenvolvimento antes de criar o novo holdout. Essa validação atingiu 100% nos
sete casos, com seis mutações efetivas recusadas. O próximo marco é congelar um
novo holdout; o anterior permanece inconclusivo e não será reutilizado.
O segundo holdout válido atingiu 100% nos onze casos: controle aceito, dez
mutações inéditas recusadas e nenhuma transformação nula. A fronteira selada
está autorizada a avançar para uma integração experimental opt-in com falha
fechada e telemetria sem conteúdo sensível. Modelo local, corpus privado e
runtime padrão continuam bloqueados.
O gateway dessa integração foi implementado desabilitado por padrão e sem
cliente de LLM. Em modo experimental, ele somente retorna request após
compilação e renderização aprovadas; budget ou contratos inválidos falham
fechados com códigos genéricos. A telemetria omite consultas, textos e IDs. O
próximo marco é avaliar essa fronteira de integração antes de conectá-la ao
roteador principal. O desenvolvimento atingiu 100% nos cinco casos e na
segurança de emissão do request: desabilitado, budget, revisão e erro do
compilador não produziram request. O próximo marco é um holdout sintético
inédito do gateway; o roteador permanece inalterado. O holdout atingiu 100% nos
cinco casos e na segurança de emissão. O próximo marco é injetar o gateway como
dependência opcional do roteador, sem mudar o padrão desabilitado e sem chamar
modelo.
Essa injeção foi implementada por um método composto separado, preservando a
API de recuperação existente. Testes cobrem padrão desabilitado, ativação
experimental, rota direta e decomposição sem executor. O próximo marco é
avaliar a integração roteador-gateway como unidade antes de qualquer síntese.
Essa avaliação atingiu 100% nos sete fluxos e na segurança de emissão de
request. O holdout integrado posterior preservou 100% na segurança de emissão,
mas obteve 83,3% (5/6) de correspondência: uma consulta que combinava origem
externa e atualidade foi classificada como recuperação direta. A candidata não
foi promovida. O próximo marco é desenvolver uma regra composicional para essa
classe de dependência externa em dados sintéticos separados e só então, se os
gates passarem, congelar outro holdout inédito. A candidata composicional
posterior atingiu 100% nos dez fluxos e na segurança de emissão, distinguindo
consulta externa atual de menções documentais estáticas. O próximo marco é
congelar um novo holdout com formulações e controles inéditos. Esse segundo
holdout atingiu 100% nos dez casos e na segurança de emissão. A fronteira
integrada está aprovada somente como caminho experimental opt-in. O próximo
marco é uma camada de orquestração desabilitada por padrão, validada primeiro
com cliente falso e dados sintéticos. Essa camada foi implementada separadamente
e atingiu 100% nos sete fluxos e na segurança de liberação: resposta bruta nunca
é exposta, e somente saída grounded validada pode atravessar a fronteira. O
holdout sintético posterior atingiu 100% nos nove casos e na segurança de
liberação, incluindo bloqueios anteriores ao cliente, violações de contrato e
timeout. O próximo marco é uma composição de aplicação opt-in que encadeie o
pipeline e o orquestrador sem alterar o comportamento padrão. Nenhum modelo foi
liberado. Essa composição foi implementada e atingiu 100% nos seis fluxos, na
segurança de invocação e na segurança de liberação, usando somente cliente falso
e dados sintéticos. O próximo marco é um holdout inédito da aplicação completa;
esse holdout atingiu 100% nos nove casos, na segurança de invocação e na
segurança de liberação. A arquitetura completa está aprovada apenas com cliente
falso. O próximo marco é um benchmark sintético controlado do modelo local por
essa aplicação, medindo conteúdo, grounding, repetibilidade e latência. Corpus
privado e runtime permanecem bloqueados. Esse benchmark executou 12 tentativas
pela aplicação: 100% dos requests foram preparados, chamados uma única vez e
validados, mas a acurácia de status foi 25% e a de conteúdo nos casos
respondíveis foi 0%. O modelo se absteve de forma estável mesmo quando as duas
evidências continham a resposta. A promoção foi rejeitada. O próximo marco é
diagnosticar o request compilado vigente contra a configuração local
anteriormente bem-sucedida em desenvolvimento sintético separado, sem abrir
novo holdout. O teste seguinte alterou somente a instrução explícita: as nove
tentativas respondíveis falharam fechadas no cliente antes da validação, e as
três abstentions esperadas continuaram válidas. A política isolada foi
rejeitada. O próximo marco acrescenta somente o schema limitado já validado em
desenvolvimento anterior. A combinação limitada posterior atingiu 12/12 em
preparação, validação e status, 9/9 em conteúdo respondível e estabilidade exata
nos quatro casos. A configuração avançou somente para a criação de um holdout
sintético inédito; runtime e corpus privado seguem bloqueados. No holdout, as
18 saídas foram estruturalmente válidas, mas a acurácia de status caiu para
66,7% e a de conteúdo respondível para 75%. O caso adversarial e os dois casos
insuficientes falharam estavelmente. A candidata foi rejeitada; o conjunto
encerrado não será usado para ajuste.
Uma fronteira de verificação independente foi adicionada depois da validação
grounded. Em sete fluxos com verificadores falsos, atingiu 100% de
correspondência e segurança de liberação, incluindo rejeição, revisão humana e
falha fechada. A arquitetura está validada, mas nenhuma estratégia semântica de
verificação foi aprovada ainda.
A primeira candidata lexical atingiu 100% de liberação segura, mas somente
33,3% de bloqueio dos casos inseguros. Uma expansão não suportada e uma
contradição de valor mantiveram sobreposição lexical suficiente para passar.
A candidata foi rejeitada sem holdout; o próximo experimento deve representar
fatos verificáveis de forma estruturada ou usar verificação independente.
O experimento estruturado subsequente restringiu o domínio a quantidades com
unidade, códigos e polaridade. Depois de corrigir apenas a normalização de duas
flexões no conjunto de desenvolvimento, atingiu 10/10 e 100% nos grupos seguro,
inseguro e revisão. A candidata pode avançar somente para um holdout sintético
inédito e previamente congelado; nele repetiu 10/10 e 100% em todos os grupos.
Está aprovada somente como componente experimental opt-in para esses três tipos;
fatos não reconhecidos continuam em revisão e o holdout está encerrado.
A integração opt-in subsequente percorreu a aplicação completa e atingiu 7/7,
com 100% de segurança de liberação. Desligar o verificador preservou o
comportamento anterior; quando ligado, contradições foram rejeitadas e linguagem
fora do domínio ficou retida sem resposta. O holdout congelado da integração
repetiu 9/9 e 100% de segurança de liberação; está encerrado, e a composição
permanece experimental e opt-in.
No benchmark seguinte com Qwen3-4B, o controle sem verificador atingiu 100% de
conteúdo e segurança em 12 tentativas. A verificação manteve a segurança, mas
reteve seis respostas corretas e reduziu o conteúdo respondível para 33,3%.
A composição local foi rejeitada sem holdout. O próximo ciclo avança para regras
estruturadas, preservando o verificador como experimento estreito.
O primeiro baseline de regras estruturadas atingiu 8/8 em desenvolvimento.
Ele preserva vigência, prioridade, condições e provenance, envia conflitos para
revisão e representa ausência de regra explicitamente. A auditoria estática
seguinte encontrou exatamente dois conflitos e uma redundância esperados em
nove regras sintéticas, sem alertar os controles incompatíveis. Ela está
aprovada como diagnóstico.
O gate subsequente atingiu 5/5 em desenvolvimento e manteve a precedência de
conflitos mesmo quando outra redundância do catálogo havia sido revisada.
No holdout congelado, a composição repetiu 6/6; o hash foi verificado e uma
segunda chamada foi recusada antes da avaliação para proteger o relatório.
A fronteira de publicação subsequente atingiu 9/9 em desenvolvimento. Ela não
avançou imediatamente para holdout enquanto aposentadorias legítimas não tinham
contrato explícito. O incremento seguinte chegou a 11/11: aposentadoria completa
foi publicada, aprovação parcial permaneceu em revisão e referências antigas ou
incompatíveis foram recusadas.
No holdout congelado da publicação, a composição atingiu 8/8; o hash coincidiu
com o congelado e uma segunda chamada foi recusada antes da avaliação.

Os números e decisões dos experimentos generativos estão em
[Resultados](results/README.md). A composição técnica vigente está em
[Arquitetura atual](architecture.md).
