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
- [Resultado 022: gate determinístico de segurança da evidência](022-deterministic-evidence-safety-gate-development.md)
- [Resultado 023: holdout do gate determinístico de segurança](023-deterministic-evidence-safety-gate-holdout.md)
- [Resultado 024: compilação de contexto em desenvolvimento](024-context-compilation-development.md)
- [Resultado 025: holdout da compilação de contexto](025-context-compilation-holdout.md)
- [Resultado 026: renderer de contexto em desenvolvimento adversarial](026-compiled-context-renderer-adversarial-development.md)
- [Resultado 027: holdout do renderer de contexto compilado](027-compiled-context-renderer-holdout.md)
- [Resultado 028: renderer de contexto selado em desenvolvimento](028-sealed-context-renderer-development.md)
- [Resultado 029: holdout do renderer de contexto selado](029-sealed-context-renderer-holdout.md)
- [Resultado 030: harness de contexto selado em desenvolvimento](030-sealed-context-harness-development.md)
- [Resultado 031: segundo holdout do renderer de contexto selado](031-sealed-context-renderer-holdout-v2.md)
- [Resultado 032: gateway de contexto compilado em desenvolvimento](032-compiled-context-gateway-development.md)
- [Resultado 033: holdout do gateway de contexto compilado](033-compiled-context-gateway-holdout.md)
- [Resultado 034: integração roteador-gateway em desenvolvimento](034-routed-compiled-integration-development.md)
- [Resultado 035: holdout da integração roteador-gateway](035-routed-compiled-integration-holdout.md)
- [Resultado 036: composição de dependência externa em desenvolvimento](036-external-dependency-composition-development.md)
- [Resultado 037: segundo holdout da integração roteador-gateway](037-routed-compiled-integration-holdout-v2.md)
- [Resultado 038: orquestração de síntese em desenvolvimento](038-synthesis-orchestration-development.md)
- [Resultado 039: holdout da orquestração de síntese](039-synthesis-orchestration-holdout.md)
- [Resultado 040: aplicação de síntese em desenvolvimento](040-synthesis-application-development.md)
- [Resultado 041: holdout da aplicação de síntese](041-synthesis-application-holdout.md)
- [Resultado 042: modelo local pela aplicação de síntese](042-local-synthesis-application-development.md)
- [Resultado 043: política explícita no request compilado](043-compiled-answer-policy-development.md)
