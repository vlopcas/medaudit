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
