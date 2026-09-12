# Resultados de experimentos

Cada experimento versionado deve registrar:

- hipótese e baseline;
- versão do código e configuração não sensível;
- identificador local do snapshot de dados, sem nomes ou conteúdo dos arquivos;
- métricas de qualidade, custo e latência;
- análise de erros e conclusão;
- decisão de manter, alterar ou remover a abordagem.

Resultados públicos devem usar somente exemplos sintéticos e passar por revisão
para evitar a exposição indireta do corpus privado.

## Experimentos

- [Resultado 001: baseline BM25 sintético](001-bm25-synthetic-baseline.md)
- [Resultado 002: RAG sintético com LLM local](002-local-llm-synthetic-rag.md)
- [Resultado 003: holdout sintético do RAG local](003-local-llm-synthetic-holdout.md)
- [Resultado 004: baseline determinístico de Query Understanding](004-deterministic-query-understanding-baseline.md)
- [Resultado 005: holdout sintético de Query Understanding](005-query-understanding-synthetic-holdout.md)
- [Resultado 006: Query Understanding híbrido com LLM local](006-local-llm-query-understanding-development.md)
- [Resultado 007: roteamento de consultas em camadas](007-layered-query-routing-development.md)
