# Documentação

Esta pasta é simultaneamente a documentação versionada do Medaudit e um vault
do Obsidian. Seu conteúdo deve continuar navegável tanto no Obsidian quanto no
GitHub, sem depender de plugins.

## Convenções de links

Use links Markdown relativos ao arquivo atual:

```markdown
[Plano de estudos](plano_estudos_llm_rag_graph_agentic.md)
[ADR-001](decisions/ADR-001-private-data-governance.md)
```

Não use caminhos absolutos locais. Evite adotar `[[wikilinks]]` como padrão,
pois eles não mantêm a mesma portabilidade fora do Obsidian. Ao renomear ou
mover um documento, atualize também todos os links que apontam para ele.

## Organização

```text
docs/
├── README.md       entrada e convenções do vault
├── architecture.md arquitetura vigente do sistema
├── decisions/      Architecture Decision Records (ADRs)
├── results/        resultados reproduzíveis dos experimentos
└── assets/         imagens e anexos públicos da documentação
```

O plano principal está em
[Plano de estudos](plano_estudos_llm_rag_graph_agentic.md). A primeira decisão
arquitetural está em
[ADR-001](decisions/ADR-001-private-data-governance.md).
O contrato entre parsing e chunking está em
[ADR-002](decisions/ADR-002-parsing-chunking-boundary.md).
Os adaptadores locais estão documentados em
[ADR-003](decisions/ADR-003-local-document-parsers.md).
O fallback de OCR está documentado em
[ADR-004](decisions/ADR-004-explicit-local-ocr.md).
O ambiente reproduzível está documentado em
[ADR-005](decisions/ADR-005-containerized-development.md).
O catálogo privado está documentado em
[ADR-006](decisions/ADR-006-private-document-catalog.md).

## Conteúdo permitido

Somente documentação e anexos próprios, sintéticos ou autorizados podem ser
versionados aqui. Documentos privados, nomes de arquivos confidenciais,
extrações e outros derivados do corpus local devem permanecer em `data/`, de
acordo com a [política de dados](../data/README.md).

O diretório `.obsidian/` é configuração local e está ignorado pelo Git.
