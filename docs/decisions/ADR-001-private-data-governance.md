# ADR-001: Governança dos documentos privados

## Status

Aceita em 2026-09-08.

## Contexto

O projeto utiliza localmente documentos institucionais que não podem ser
publicados. Nomes de arquivos, versões, conteúdo extraído e artefatos derivados
também podem revelar informações sobre o acervo. A licença MIT do repositório
não transfere direitos sobre materiais de terceiros.

## Opções consideradas

1. Versionar os documentos diretamente no Git.
2. Usar Git LFS para os documentos.
3. Manter os documentos fora do histórico e gerar um inventário privado local.

Git LFS reduziria o impacto dos binários no histórico, mas não resolveria
confidencialidade nem direitos de redistribuição.

## Decisão

Todo o conteúdo de `data/` será privado e ignorado por padrão. Somente o README
de governança e marcadores de diretórios poderão ser versionados. Inventários,
extrações, índices e benchmarks derivados serão locais, salvo quando forem
integralmente sintéticos e revisados antes da publicação.

O inventário local conterá metadados técnicos e SHA-256 para permitir
reprodutibilidade sem incorporar documentos ao Git.

## Consequências

- Um novo ambiente não recebe automaticamente o corpus real.
- Cada colaborador autorizado deve provisionar os documentos separadamente.
- Resultados que dependam do corpus devem registrar um identificador local do
  snapshot, sem publicar o manifesto.
- Casos e fixtures versionados precisam ser sintéticos.

## Como validar

- `git status --ignored data/` deve mostrar os documentos reais como ignorados.
- `git check-ignore data/<arquivo-privado>` deve confirmar a proteção.
- Testes automatizados não podem depender do acervo local.

