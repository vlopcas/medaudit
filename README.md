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
dados sintéticos e sem depender de API ou LLM. Consulte a
[arquitetura atual](docs/architecture.md).

## Ambiente de desenvolvimento

Requer Python 3.12 ou superior.

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
