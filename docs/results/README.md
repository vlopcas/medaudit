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
- [Resultado 008: decomposição estrutural de consultas](008-structural-decomposition-holdout.md)
- [Resultado 009: holdout do roteamento explícito](009-explicit-query-routing-holdout.md)
- [Resultado 010: holdout do planejamento determinístico](010-deterministic-query-planning-holdout.md)
- [Resultado 011: holdout da execução de decomposição](011-decomposition-execution-holdout.md)
- [Resultado 012: holdout do agrupamento de evidências](012-evidence-aggregation-holdout.md)
- [Resultado 013: holdout da validação grounded decomposta](013-decomposed-grounding-validation-holdout.md)
- [Resultado 014: síntese decomposta com LLM local](014-local-decomposed-grounding-development.md)
- [Resultado 015: repetibilidade da síntese decomposta](015-local-decomposed-grounding-repeatability.md)
- [Resultado 016: política explícita de resposta](016-explicit-answer-policy-development.md)
- [Resultado 017: limite de saída da síntese local](017-local-output-token-limit.md)
- [Resultado 018: schema limitado da síntese local](018-bounded-generation-schema-development.md)
- [Resultado 019: holdout da síntese decomposta local](019-local-decomposed-grounding-holdout.md)
- [Resultado 020: diagnóstico de instruções não confiáveis](020-untrusted-evidence-instruction-diagnostics.md)
- [Resultado 021: endurecimento do prompt contra instruções](021-security-hardened-prompt-development.md)
