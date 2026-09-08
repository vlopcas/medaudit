# Dados locais e privados

Esta pasta recebe documentos de referência usados localmente no estudo de
auditoria documental. Eles podem incluir materiais provenientes de entidades
do setor de saúde suplementar, operadoras, órgãos reguladores e outras fontes
institucionais legitimamente acessadas pelo responsável pelo projeto.

Os arquivos reais, seus nomes, metadados, conteúdos extraídos e artefatos
derivados são confidenciais e **não fazem parte da distribuição pública** deste
repositório. A licença MIT do projeto se aplica ao código e à documentação
autoral, não concede direitos sobre documentos de terceiros e não autoriza sua
redistribuição.

## Regras de uso

- não adicionar documentos reais ao Git, releases, issues ou pull requests;
- não copiar trechos reais para testes, exemplos, logs ou documentação;
- usar somente dados sintéticos e desidentificados em artefatos versionados;
- confirmar base legal, autorização e política do fornecedor antes de enviar
  qualquer documento a uma API externa;
- evitar dados pessoais e assistenciais; se forem indispensáveis, aplicar
  minimização, controle de acesso e desidentificação adequados;
- manter resultados derivados dos documentos dentro das pastas ignoradas;
- revisar manualmente todo artefato antes de publicá-lo.

## Organização local

```text
data/
├── raw/                documentos originais, imutáveis
├── processed/          texto, tabelas e metadados derivados
├── synthetic_cases/    casos integralmente sintéticos
├── eval/               benchmark local e respostas esperadas
└── manifest.local.json inventário técnico gerado localmente
```

Arquivos que já estejam diretamente em `data/` podem ser migrados para
`data/raw/` localmente quando conveniente. Essa movimentação não é necessária
para protegê-los: todo o conteúdo da pasta já é ignorado, exceto este README,
os marcadores vazios e conjuntos JSON explicitamente revisados e sintéticos em
`synthetic_cases/` e `eval/`.

O inventário local registra apenas caminho relativo, tamanho, extensão,
horário de modificação e SHA-256. Ele não lê nem extrai o conteúdo documental:

```bash
medaudit-inventory --input data --output data/manifest.local.json
```

Para testar localmente os parsers sem persistir texto extraído, gere um
diagnóstico privado. O terminal exibe somente contagens agregadas; detalhes com
nomes de arquivos permanecem no relatório ignorado:

```bash
medaudit-profile-corpus \
  --input data \
  --output data/corpus-profile.local.json
```

O status `needs_ocr` indica PDF sem camada textual extraível. OCR é opcional e
local; antes de habilitá-lo, confirme que `tesseract --list-langs` contém o
idioma necessário. A ausência do mecanismo local gera erro explícito e nunca
aciona automaticamente um serviço externo.

## Catálogo documental privado

O catálogo separa identidade técnica de metadados semânticos revisados. Sua
primeira execução cria entradas pendentes; execuções seguintes preservam os
campos preenchidos, reconhecem cópias pelo SHA-256 e marcam arquivos ausentes:

```bash
medaudit-build-catalog \
  --input data \
  --output data/catalog.local.json
```

Preencha manualmente família, organização, versão, vigência e relações de
substituição. Não marque uma entrada como `reviewed` antes de confirmar esses
campos no próprio documento. O catálogo contém nomes e metadados privados e não
deve ser publicado.

`data/catalog.local.json` é a fonte revisada. Cópias incompletas e backups
também permanecem privados, mas não são consumidos pelo pipeline. No Docker,
`catalog-bootstrap` gera uma proposta separada em `artifacts/`; ele nunca
sobrescreve a fonte revisada. Valide-a com:

```bash
docker compose run --rm catalog-check
```

O comando aceita datas ISO (`AAAA-MM-DD`) ou timestamps ISO e imprime somente
contagens agregadas.

O processamento usa `data/catalog.local.json`, mas grava chunks apenas em
`artifacts/chunks.local.jsonl`. A data de referência é obrigatória no comando
Python e explícita via `REFERENCE_DATE` no Docker. Os chunks contêm texto
privado e nunca devem ser publicados.

## Golden set privado de retrieval

Copie `data/eval/private_retrieval_template.json` para
`data/retrieval-eval.local.json` e substitua todos os placeholders. A
`reference_date` precisa ser igual à usada para gerar os chunks. Comece
rotulando `relevant_document_ids`; use `relevant_chunk_ids` somente quando a
localização exata já tiver sido revisada. Um caso não pode misturar os dois
níveis. Perguntas deliberadamente sem resposta usam ambas as listas vazias.

Execute a baseline lexical com:

```bash
docker compose run --rm evaluate-private-bm25
```

O terminal mostra somente métricas agregadas. O relatório por caso permanece
em `artifacts/retrieval-eval.local.json` e não inclui o texto das perguntas.
