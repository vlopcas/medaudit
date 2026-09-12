# Medaudit

Projeto educacional e evolutivo para estudar LLMs, recuperação de informação,
RAG, processamento documental, regras estruturadas, grafos e fluxos agênticos
aplicados à auditoria documental.

O princípio central é adicionar complexidade somente quando uma avaliação
reproduzível demonstrar a limitação do baseline atual. O plano completo está em
[`docs/plano_estudos_llm_rag_graph_agentic.md`](docs/plano_estudos_llm_rag_graph_agentic.md).

> Este software auxilia estudos e análise documental. Ele não substitui
> auditoria profissional, decisão clínica, regulatória ou de cobertura.
> Conclusões de alto impacto exigem validação humana.

## Estado atual

A fundação da Fase 0 está concluída. O projeto possui um baseline BM25 local e
os primeiros contratos de parsing e chunking estrutural, todos avaliados com
dados sintéticos e sem depender de API ou LLM. A ingestão seleciona parsers por
uma allowlist de tipos de mídia e produz artefatos locais versionados. Consulte a
[arquitetura atual](docs/architecture.md).

O pipeline de RAG já possui uma fronteira determinística entre retrieval e
geração: somente evidências aceitas pela política congelada podem formar um
prompt, e a resposta estruturada só aceita citações presentes nesse contexto.
O primeiro adaptador generativo aponta exclusivamente para um servidor
`llama.cpp` em loopback e usa JSON Schema. O modelo local ainda não é baixado
nem iniciado pelos serviços atuais, e nenhuma API externa é chamada durante a
inferência.

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
