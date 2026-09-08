# ADR-002: Separação entre parsing e chunking

## Status

Aceita em 2026-09-08.

## Contexto

O corpus local contém formatos e estruturas diferentes. Estratégias de
chunking precisarão ser comparadas sobre a mesma interpretação documental sem
acoplar a extração de PDF ou planilha a uma estratégia de retrieval.

## Opções consideradas

1. Cada parser produzir diretamente chunks prontos para indexação.
2. Parsers produzirem somente texto contínuo.
3. Parsers produzirem elementos normalizados, seguidos por chunkers separados.

## Decisão

Adotar uma representação intermediária composta por elementos ordenados com
tipo, página, seção e identificador determinístico. Parsers específicos por
formato produzem essa representação; estratégias independentes a transformam
em chunks.

O primeiro chunker respeita limites de página e seção e usa tamanho em
caracteres apenas como baseline simples. Tabelas e figuras são elementos
atômicos. Limites por tokens e outras estratégias serão experimentos futuros,
não alterações implícitas deste baseline.

## Consequências

- parsing caro poderá ser reutilizado entre experimentos de chunking;
- proveniência existe antes do retrieval;
- cada adaptador deverá mapear fielmente estruturas do formato de origem;
- mudanças na representação intermediária exigirão versionamento de artefatos;
- elementos individuais maiores que o limite permanecem inteiros e deverão ser
  tratados por uma estratégia especializada no futuro.

## Como validar

- IDs idênticos devem ser gerados para a mesma entrada e configuração;
- chunks não devem cruzar páginas ou seções;
- todo chunk deve informar os elementos de origem e a versão documental;
- testes públicos devem usar exclusivamente fixtures sintéticas.
