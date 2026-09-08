# Arquitetura atual

Esta página descreve apenas o que já existe. A arquitetura-alvo mais ampla está
no [plano de estudos](plano_estudos_llm_rag_graph_agentic.md).

## Fluxo documental

```text
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
    ↓ BM25Index
SearchResult[]
    ↓ evaluation
Hit Rate / Recall / MRR / abstention
```

## Limites dos módulos

- `documents`: modelos de domínio sem dependência de formato ou fornecedor;
- `parsing`: adaptadores que convertem bytes em elementos normalizados;
- `chunking`: estratégias intercambiáveis sobre a representação normalizada;
- `retrieval`: índices e resultados de busca;
- `evaluation`: datasets, métricas e execução de benchmarks;
- `llm`: contrato futuro, ainda sem adaptador externo;
- `ingestion`: inventário, seleção de parser, pipeline local e serialização.

O parser inicial aceita texto UTF-8 sintético. Adaptadores para PDF e planilhas
ainda não foram escolhidos. O chunker inicial usa caracteres, respeita páginas
e seções e mantém tabelas e figuras isoladas.

O registro de parsers falha para tipos desconhecidos ou ambíguos. O pipeline
não acessa rede nem armazenamento: recebe bytes e retorna um resultado. A
persistência é uma responsabilidade separada e seus artefatos devem permanecer
em `data/processed/`, que é ignorado pelo Git.

## Decisões relacionadas

- [ADR-001: governança dos dados privados](decisions/ADR-001-private-data-governance.md)
- [ADR-002: separação entre parsing e chunking](decisions/ADR-002-parsing-chunking-boundary.md)
