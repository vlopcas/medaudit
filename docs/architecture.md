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
- `llm`: contrato futuro, ainda sem adaptador externo;
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

## Ambiente de execução

Docker Compose é a referência reproduzível. A imagem contém Python e OCR, mas
não contém o corpus privado. Os serviços executam sem rede, com filesystem raiz
somente leitura e sem capabilities adicionais. O corpus entra apenas por bind
mount somente leitura; artefatos locais saem por um mount separado e ignorado.
