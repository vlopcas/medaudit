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

Para criar ou atualizar o catálogo privado que será revisado manualmente:

```bash
docker compose run --rm catalog
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
