# Medaudit

Projeto educacional e evolutivo para estudar LLMs, recuperação de informação,
RAG, processamento documental, regras estruturadas, grafos e fluxos agênticos
aplicados à auditoria documental.

O princípio central é adicionar complexidade somente quando uma avaliação
reproduzível demonstrar a limitação do baseline atual. O plano completo está em
[roadmap canônico](docs/roadmap.md), o currículo detalhado permanece no
[plano de estudos](docs/plano_estudos_llm_rag_graph_agentic.md) e o progresso
observado está consolidado no
[`status do plano`](docs/study-progress.md).

> Este software auxilia estudos e análise documental. Ele não substitui
> auditoria profissional, decisão clínica, regulatória ou de cobertura.
> Conclusões de alto impacto exigem validação humana.

## Estado atual

A fundação e o pipeline documental local estão implementados: inventário,
catálogo revisado, parsing de texto, PDF e planilhas, OCR explícito, chunking
estrutural e materialização por vigência. O projeto também possui avaliação
privada reproduzível, snapshots temporais e uma política congelada de confiança
para decidir entre recuperar evidências ou se abster.

BM25 permanece como baseline principal. Recuperação densa, fusão híbrida e
reranking semântico foram implementados e comparados na calibração, mas ainda
não demonstraram ganho suficiente para substituir o baseline. Esses caminhos
continuam experimentais.

O primeiro RAG condicionado a evidências funciona ponta a ponta com um servidor
`llama.cpp` local, saída restringida por JSON Schema e validação determinística
de citações. O modelo fixado foi baixado e executado com aceleração por GPU em
um ambiente Docker isolado. Embora o contrato estrutural tenha funcionado, o
modelo completou apenas 3 de 7 respostas no holdout sintético congelado. Por
isso, geração sobre o corpus privado permanece desabilitada.

A etapa atual é a **Fase 8 — Query Understanding**. Consulte a
[arquitetura atual](docs/architecture.md), o
[status detalhado do plano](docs/study-progress.md) e os
[resultados dos experimentos](docs/results/README.md).

O baseline determinístico inicial dessa fase pode ser avaliado, sem rede e
somente com perguntas sintéticas, usando:

```bash
docker compose run --rm evaluate-query-understanding
```

Depois de ajustar somente as falhas observadas nesse conjunto de
desenvolvimento, abra uma única vez o holdout sintético congelado com:

```bash
docker compose run --rm evaluate-query-understanding-holdout
```

O comando valida o SHA-256 do dataset e recusa sobrescrever o relatório em
`artifacts/query-understanding-holdout.local.json`.

A variante híbrida que usa o LLM local somente para sinais semânticos pode ser
reproduzida sobre dados sintéticos com:

```bash
docker compose run --rm benchmark-local-query-understanding
docker compose stop llm-server
```

Ela obteve 56,25% de exact match no desenvolvimento e foi rejeitada antes de
qualquer holdout ou integração ao RAG.

A heurística estrutural de decomposição pode ser reproduzida no conjunto de
desenvolvimento com:

```bash
docker compose run --rm evaluate-structural-decomposition
```

Seu holdout congelado já foi executado e rejeitou a hipótese com 62,5% de
acurácia; ela não integra o fluxo principal.

O roteamento explícito promovido pode ser avaliado no desenvolvimento com
`docker compose run --rm evaluate-explicit-query-routing`. Seu holdout
congelado atingiu 100% em 15 casos. No runtime, somente a rota direta toca no
retriever. A decomposição produz apenas um plano determinístico ou um pedido de
esclarecimento; dependência externa encerra sem executar ações.

O planejamento de decomposição pode ser reproduzido no desenvolvimento com
`docker compose run --rm evaluate-query-planning`. Seu holdout sintético
congelado atingiu 100% em 12 casos; por padrão, os passos planejados não
executam buscas nem síntese.

O executor opt-in dos passos pode ser avaliado com
`docker compose run --rm benchmark-decomposition-execution`. Seu holdout
congelado atingiu 100% em 10 casos e 17 passos. A execução temporal exige um
resolvedor explícito de snapshots e ainda não combina evidências nem gera uma
resposta comparativa.

As evidências executadas são agrupadas por passo sem perder escopo, data ou
citações. O agrupador atingiu 100% em quatro casos e sete grupos no holdout e é
incluído automaticamente quando o executor opt-in está configurado. O pacote
ainda não chama o modelo generativo.

O contrato de síntese decomposta exige afirmações atômicas com citações ligadas
ao grupo correto. Seu validador adversarial atingiu 100% em oito casos de
holdout. No benchmark de desenvolvimento com o `Qwen3-4B Q4_K_M`, o modelo
respeitou a estrutura, mas respondeu corretamente apenas um dos quatro casos
respondíveis. Em três repetições por caso, apenas 33,3% dos status ficaram
corretos e um caso variou entre resposta e abstention; por isso a síntese
decomposta continua fora do runtime e não foi avaliada em holdout. Uma política
de prompt explícita alcançou uma rodada perfeita de 15 tentativas, mas outra
rodada teve uma geração inválida de aproximadamente 119 segundos. A candidata
permanece experimental. Um limite de 512 tokens reduziu a pior latência para
6,88 segundos, mas ainda houve uma tentativa truncada e inválida em 30. O
schema limitado seguinte atingiu 30/30 tentativas válidas, grounded e corretas
em duas rodadas; a configuração agora está elegível somente para um novo
holdout sintético congelado, não para o runtime. Os protocolos podem ser
reproduzidos com
`docker compose run --rm benchmark-local-decomposed-grounding` e
`docker compose run --rm benchmark-local-decomposed-grounding-prompt`; a versão
limitada usa `docker compose run --rm benchmark-local-decomposed-grounding-capped`.
A variante com schema limitado usa
`docker compose run --rm benchmark-local-decomposed-grounding-bounded`.

O holdout inédito dessa variante atingiu 100% em estrutura, grounding e status,
além do mínimo de 80% em conteúdo. Entretanto, falhou nas três repetições do
caso com instrução não confiável inserida na evidência. O resultado agregado não
autoriza o runtime: o próximo ciclo é um diagnóstico sintético de segurança,
sem reutilizar o holdout para ajustes. Esse diagnóstico recuperou todos os fatos
corretos, mas repetiu conceitos proibidos em 6/18 tentativas, concentradas em
marcadores falsos de sistema e JSON inserido na evidência. Um prompt endurecido
elevou a taxa para 83,3%, porém deslocou a falha para overrides em inglês. Essa
abordagem foi rejeitada; o próximo passo é um gate determinístico de evidência
suspeita com revisão explícita. O gate isolado atingiu 100% de recall em seis
ataques e 100% de especificidade em seis textos legítimos semelhantes no
desenvolvimento sintético. Ele emite somente IDs e códigos de sinal e permanece
fora do runtime até passar por holdout inédito; detecções devem levar à revisão,
não à alteração silenciosa da evidência. Esse holdout reduziu o recall de
ataques para 50% e a especificidade para 87,5%, portanto o gate foi rejeitado
para integração. O experimento mostra que enumerar padrões conhecidos não é uma
fronteira de segurança generalizável.

O próximo componente de Context Engineering já possui um contrato isolado e
provider-neutral. Ele separa instrução, consulta e evidências, aplica orçamento,
preserva provenance e bloqueia geração parcial ou dependente de itens em
revisão. Ainda não renderiza prompts nem integra o runtime; primeiro será
avaliado em datasets sintéticos próprios. O desenvolvimento inicial atingiu
100% em seis casos de seleção, budget, revisão, deduplicação e evidência
insuficiente; a candidata agora está autorizada somente a enfrentar um holdout
inédito. O holdout posterior atingiu 100% em oito casos limítrofes. O contrato
está autorizado a ganhar uma integração opt-in com a síntese decomposta, mas o
modelo local e o corpus privado permanecem bloqueados. O renderer opt-in agora
produz o mesmo `LLMRequest` anterior somente para contextos `ready` e revalida
budget, confiança, IDs e vínculos por passo; ele ainda não controla o runtime.
No desenvolvimento adversarial, aceitou o controle íntegro e recusou 12/12
mutações inseguras. A fronteira ainda precisa passar por holdout estrutural
inédito antes de qualquer ativação.
Esse holdout reprovou o renderer com apenas 25% de correspondência exata e
28,57% de rejeição das mutações inseguras. Alterações pós-compilação de conteúdo
e topologia não foram detectadas; a integração permanece bloqueada até existir
uma representação canônica selada e novamente avaliada. A nova candidata já
calcula um SHA-256 determinístico sobre todo o contexto representado e o
renderer verifica o selo antes de usar qualquer campo, além de manter
invariantes explícitas de topologia. Ela permanece fora do runtime e ainda
precisa passar por desenvolvimento adversarial e por um novo holdout. O
desenvolvimento adversarial seguinte atingiu 100% nos 21 casos: o controle foi
aceito e as vinte mutações foram recusadas em todas as categorias. Isso autoriza
somente a criação de um novo holdout congelado; não autoriza o runtime.
O holdout posterior recusou todas as nove mutações que efetivamente alteraram o
contexto, mas três casos eram no-ops produzidos pelo adaptador do benchmark. O
resultado é inconclusivo, não uma aprovação: o próximo avaliador deve recusar
mutações nulas antes de congelarmos outro holdout. Essa pré-condição já foi
implementada, e o adaptador sintético agora preserva provenance opcional; falta
validar o harness corrigido em desenvolvimento antes de outro congelamento. A
validação posterior atingiu 100% nos sete casos, cobrindo os campos antes
descartados e outras associações. O instrumento está autorizado a produzir um
novo holdout, mas o renderer continua fora do runtime. O segundo holdout passou
em 11/11 casos, com dez mutações inéditas recusadas e nenhuma mutação nula. A
fronteira está aprovada apenas para uma integração experimental e opt-in, ainda
sem habilitar modelo local ou corpus privado. Essa integração agora existe como
um gateway desabilitado por padrão: em modo experimental, ele compila e renderiza
somente contextos aprovados; em qualquer bloqueio não produz `LLMRequest`. Sua
telemetria contém apenas estados, códigos, contagens, tokens e duração. O gateway
não possui cliente de modelo e ainda não está conectado ao roteador principal.
No desenvolvimento sintético, ele atingiu 5/5 em correspondência exata e
segurança de emissão: somente o caso preparado recebeu request. O próximo gate
é um holdout próprio antes de qualquer conexão ao roteador. Esse holdout atingiu
5/5 em correspondência e segurança de emissão, incluindo bundle incompleto,
revisões e evidência compartilhada. O gateway está autorizado a ser injetado no
roteador como dependência opcional, ainda desabilitada por padrão. A conexão
agora existe em `retrieve_with_compiled_request`, sem alterar `retrieve`: somente
uma decomposição executada com bundle chega ao gateway. Rotas diretas, externas
ou sem executor não produzem preparação, e nenhuma chamada de modelo foi
adicionada.
Na avaliação integrada de desenvolvimento, os sete fluxos atingiram 100% em
correspondência e segurança de emissão. Apenas a decomposição suficiente com
gateway experimental produziu request. No holdout integrado, a segurança de
emissão permaneceu em 100%, mas a correspondência caiu para 83,3% (5/6): uma
consulta inédita que combinava origem externa e atualidade foi roteada como
recuperação direta. A candidata integrada não foi promovida. O próximo ciclo
passou a exigir, para marcadores genéricos, a composição entre ação de consulta,
origem externa e atualidade. Em desenvolvimento, essa candidata atingiu 10/10
em correspondência e segurança de emissão, incluindo controles documentais
estáticos. Ela está autorizada somente a enfrentar outro holdout inédito antes
de qualquer avanço da síntese. O segundo holdout integrado atingiu 10/10 em
correspondência e segurança de emissão, incluindo formulações externas inéditas
e controles negativos. A fronteira está aprovada somente como caminho
experimental opt-in. O próximo marco é uma orquestração de síntese isolada,
desabilitada por padrão e inicialmente avaliada apenas com cliente falso e
dados sintéticos. Essa orquestração agora existe e nunca expõe a resposta bruta:
somente saída aprovada pelo validador grounded é liberada. No desenvolvimento
com clientes falsos, atingiu 7/7 em correspondência e segurança de liberação. O
holdout sintético posterior atingiu 9/9 nas duas métricas, incluindo bloqueios,
suporte combinado, respostas inválidas e timeout. A fronteira está aprovada
somente para uma composição de aplicação opt-in; modelo local, qualidade
factual e corpus privado continuam bloqueados. Essa composição agora existe sem
alterar as APIs anteriores e mantém síntese desabilitada por padrão. Na
avaliação sintética com cliente falso, atingiu 6/6 em correspondência, segurança
de invocação e segurança de liberação. O próximo gate é um holdout inédito da
operação completa. Esse holdout atingiu 9/9 nas três métricas, incluindo
temporalidade, revisão, budget, falhas do cliente e respostas inválidas. A
arquitetura está aprovada somente com cliente falso. O próximo marco é medir a
compatibilidade e a qualidade do modelo local através dessa aplicação em dados
sintéticos. Esse benchmark executou 12/12 requests preparados e liberou 12/12
saídas grounded válidas, mas obteve somente 25% de acurácia de status e 0% de
conteúdo nos casos respondíveis: o modelo se absteve de forma estável nas nove
tentativas com evidência suficiente. A promoção foi rejeitada. O próximo marco
é diagnosticar, em desenvolvimento sintético separado, a diferença entre o
request compilado vigente e a configuração local anteriormente bem-sucedida;
o primeiro teste alterou somente a instrução explícita de resposta. As nove
tentativas respondíveis terminaram em falha fechada do cliente antes da
validação, enquanto as três abstentions esperadas permaneceram válidas. A
política isolada foi rejeitada. O próximo teste acrescenta apenas o schema
limitado já conhecido. Essa combinação atingiu 12/12 em preparação, validação,
status e estabilidade, além de 9/9 em conteúdo respondível, com latência máxima
de 4,48 s. Ela está aprovada somente para um holdout sintético inédito; corpus
privado e runtime continuam bloqueados. No holdout congelado, a validação
estrutural permaneceu em 18/18, mas a acurácia de status caiu para 66,7% e a de
conteúdo respondível para 75%. O caso com instrução não confiável e os dois
casos de evidência insuficiente reprovaram de forma estável. A candidata foi
rejeitada e esse holdout não será usado para ajuste.
Uma fronteira independente de verificação agora opera depois da validação
grounded e antes da liberação. Com verificadores falsos, atingiu 7/7 em
correspondência e segurança de liberação, cobrindo rejeição, revisão humana,
falha fechada e ordem estrutural. Ainda não existe estratégia semântica
aprovada; o próximo ciclo será somente desenvolvimento sintético novo.
A primeira estratégia real combinou cobertura lexical das evidências citadas
com revisão de instruções explícitas. Ela preservou 100% dos casos seguros, mas
bloqueou somente 33,3% dos inseguros e deixou passar expansão sem suporte e
contradição de valor. Foi rejeitada no desenvolvimento e não consumirá holdout.
Uma segunda estratégia restringiu a verificação a quantidades com unidade,
códigos e polaridade. Após uma correção de flexões no próprio desenvolvimento,
ela atingiu 10/10, inclusive 100% nos grupos seguro, inseguro e revisão. A
candidata avançou para um holdout sintético inédito e congelado, no qual também
atingiu 10/10. Está aprovada apenas como componente experimental opt-in para
esses tipos; linguagem fora do domínio segue para revisão, e nenhuma
autorização foi dada ao corpus privado ou ao runtime principal.
Sua integração opt-in com a aplicação completa foi então exercitada em sete
fluxos sintéticos e atingiu 100% de correspondência e segurança de liberação.
Rejeições e revisões não expuseram respostas, e o opt-in desligado preservou o
comportamento anterior. Em holdout próprio e congelado, repetiu 100% nos nove
fluxos e na segurança de liberação. A integração está aprovada apenas como
caminho experimental opt-in dentro do domínio estreito do verificador.
Ao conectar o mesmo componente ao Qwen3-4B local, o controle sem verificador
atingiu 100% de conteúdo e segurança em 12 tentativas. O verificador manteve
100% de segurança, mas reteve seis respostas corretas e reduziu a acurácia de
conteúdo respondível para 33,3%. Essa composição foi rejeitada no
desenvolvimento e não seguirá para holdout.

## Ambiente de desenvolvimento

Requer Python 3.12 ou superior.

O caminho recomendado usa Docker e não instala bibliotecas ou Tesseract
globalmente na máquina:

```bash
mkdir -p artifacts
docker compose build
docker compose run --rm checks
```

Para analisar localmente a compatibilidade do corpus privado:

```bash
docker compose run --rm profile
```

Para repetir o diagnóstico aplicando Tesseract somente a PDFs totalmente sem
texto nativo:

```bash
docker compose run --rm profile-ocr
```

Para criar um bootstrap privado que será revisado manualmente:

```bash
docker compose run --rm catalog-bootstrap
```

O bootstrap fica em `artifacts/catalog-bootstrap.local.json`; ele não substitui
o catálogo revisado em `data/catalog.local.json`. Para validar este último sem
exibir nomes ou metadados:

```bash
docker compose run --rm catalog-check
```

Para gerar chunks privados somente das versões vigentes na data de referência:

```bash
REFERENCE_DATE=2026-09-08 docker compose run --rm process-ocr
```

O resultado fica em `artifacts/chunks.local.jsonl`. Para uma consulta histórica,
informe a data correspondente em `REFERENCE_DATE`; versões fora daquela
vigência não entram no resultado.

Depois do processamento, gere estatísticas agregadas antes de escolher uma
estratégia de indexação:

```bash
docker compose run --rm chunk-profile
```

O relatório privado fica em `artifacts/chunk-profile.local.json` e não contém o
texto nem identificadores dos documentos.

Após preencher `data/retrieval-eval.local.json` conforme
[`data/README.md`](data/README.md), execute a baseline BM25 privada:

```bash
docker compose run --rm evaluate-private-bm25
```

Use `TOP_K` e `MIN_SCORE` para experimentos reproduzíveis, por exemplo
`TOP_K=10 MIN_SCORE=2.0 docker compose run --rm evaluate-private-bm25`.

Para executar todos os golden sets temporais após uma auditoria sem conflitos:

```bash
docker compose run --rm temporal-baseline
```

O comando materializa cada snapshot, executa BM25 e grava o consolidado privado
em `artifacts/temporal-baseline/baseline.local.json`.

Para diagnosticar falhas por dificuldade, categoria e tipo de raciocínio sem
mostrar esses detalhes no terminal:

```bash
docker compose run --rm diagnose-baseline
```

Para medir sinais de confiança interpretáveis sem definir prematuramente uma
regra de abstention:

```bash
docker compose run --rm analyze-confidence
```

Depois de ampliar e revisar o benchmark, congele a separação determinística
entre calibração e avaliação final. Casos usados em experimentos anteriores
ficam obrigatoriamente em calibração; somente casos novos podem entrar na
avaliação final:

```bash
docker compose run --rm split-evaluation
```

O manifesto privado usa apenas IDs e fingerprints. O conjunto `calibration`
serve para escolher sinais e limiares; o conjunto `evaluation` permanece sem
consulta até a política estar congelada.

Os candidatos adversariais gerados com o
[prompt privado](docs/evaluation/notebooklm-adversarial-prompt.md) podem ser
anexados à revisão existente sem perder as aprovações anteriores:

```bash
docker compose run --rm prepare-adversarial-review
```

Somente os novos casos ficam pendentes no arquivo expandido.

Com o split congelado, materialize os snapshots sem executar consultas e meça
os sinais exclusivamente na calibração:

```bash
docker compose run --rm materialize-expanded-snapshots
docker compose run --rm analyze-calibration-confidence
docker compose run --rm calibrate-confidence-policy
```

Compare uma política candidata conservadora de até dois sinais com:

```bash
docker compose run --rm calibrate-multisignal-policy
```

Esse comando grava uma candidata separada e nunca substitui automaticamente a
política congelada.

Estime a estabilidade da candidata sem consultar o holdout:

```bash
docker compose run --rm cross-validate-multisignal-policy
```

A política usa um único limiar interpretável de score, mantém pelo menos 80%
dos casos respondíveis na calibração e maximiza a abstention dos casos sem
evidência. A avaliação final não participa dessa escolha.

Depois de congelar código, configuração e política, execute o holdout uma única
vez:

```bash
docker compose run --rm evaluate-heldout-policy
```

O avaliador confere o hash da calibração e recusa sobrescrever o resultado.

Para preparar o modelo de embeddings sem montar o corpus privado:

```bash
mkdir -p models
docker compose run --rm embedding-model-download
docker compose run --rm embedding-model-check
```

O primeiro comando é o único com acesso à rede. O segundo recarrega a revisão
fixada usando o cache local como somente leitura e sem rede.

Para baixar e verificar o modelo generativo local sem montar `data/`:

```bash
docker compose run --rm local-llm-download
docker compose run --rm local-llm-check
```

O GGUF fica em `models/`, é ignorado pelo Git e tem revisão e SHA-256 fixados.
Depois, execute o primeiro RAG generativo somente sobre dados sintéticos:

```bash
docker compose run --rm benchmark-local-llm
docker compose stop llm-server
```

O servidor não publica portas no host, participa apenas de uma rede Docker
interna e monta `models/` como somente leitura. O benchmark não monta `data/`
nem persiste respostas; grava somente métricas agregadas em `artifacts/`.
Consulte o [resultado sintético](docs/results/002-local-llm-synthetic-rag.md).
O modelo permanece experimental: a avaliação de conteúdo atingiu 66,7% após o
ajuste do prompt, portanto a geração sobre o corpus privado ainda não está
habilitada.

O holdout sintético congelado pode ser aberto uma única vez com
`docker compose run --rm evaluate-local-llm-holdout`. Ele já foi executado para
a configuração atual e recusará sobrescrever o relatório local. O resultado
de generalização foi insuficiente, com 3 de 7 respostas completas; consulte o
[Resultado 003](docs/results/003-local-llm-synthetic-holdout.md).

Depois de materializar os snapshots temporais, gere ou atualize o cache local
deduplicado de embeddings com:

```bash
docker compose run --rm materialize-embedding-cache
```

O comando executa sem rede, lê o modelo e os snapshots em modo somente leitura
e grava em `artifacts/` apenas IDs, hashes e vetores privados reutilizáveis.

Compare BM25, recuperação densa e RRF somente na calibração com:

```bash
docker compose run --rm benchmark-hybrid-calibration
```

O comando valida o split antes de buscar e não oferece opção para executar a
partição de avaliação final.

Gere o diagnóstico agregado das diferenças contra BM25 com:

```bash
docker compose run --rm diagnose-hybrid-calibration
```

Meça o truncamento real dos chunks com o tokenizer fixado do E5:

```bash
docker compose run --rm profile-embedding-inputs
```

Os documentos são montados como somente leitura e o relatório privado é salvo
em `artifacts/`. A execução dos containers não possui acesso à rede e os
relatórios não armazenam texto extraído.

Como alternativa, use um ambiente virtual nativo:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
pytest
ruff check .
mypy src
```

## Dados privados

Os documentos reais ficam exclusivamente em `data/` e são ignorados pelo Git.
Consulte [`data/README.md`](data/README.md) antes de trabalhar com eles. Para
gerar um inventário técnico local, sem ler o conteúdo dos arquivos:

```bash
medaudit-inventory --input data --output data/manifest.local.json
```

O manifesto resultante também é privado e não deve ser publicado.

## Baseline de retrieval

Execute a avaliação lexical reproduzível com:

```bash
medaudit-evaluate-bm25 \
  --corpus data/synthetic_cases/corpus.json \
  --cases data/eval/bm25_cases.json \
  --top-k 3 \
  --min-score 3.0
```

O limiar é experimental e específico do pequeno benchmark atual. Consulte o
[primeiro resultado](docs/results/001-bm25-synthetic-baseline.md) para métricas,
limitações e próximos passos.

## Estrutura

```text
data/                  documentos locais, derivados e casos sintéticos
docs/decisions/        Architecture Decision Records (ADRs)
docs/results/          resultados reproduzíveis dos experimentos
src/medaudit/          código da aplicação
tests/                 testes automatizados com dados sintéticos
```

O código é distribuído sob a licença MIT. Essa licença não se estende aos
documentos privados utilizados localmente.
