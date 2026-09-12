# Resultado 003: holdout sintético do RAG local

## Hipótese e protocolo

O prompt escolhido no Resultado 002 deveria generalizar para casos sintéticos
novos sem ajuste adicional. Antes da execução foram congelados:

- 10 casos: 7 respondíveis e 3 sem evidência;
- categorias de busca exata, quantidade, negação, exceção, versão,
  multi-documento, factual e evidência ausente;
- corpus e respostas esperadas integralmente sintéticos;
- fingerprints SHA-256 dos dois arquivos;
- BM25 com `top_k=3`, limiar sintético 3 e o mesmo prompt `/no_think`;
- métricas de gate, conteúdo, conceitos, status e citações;
- caminho de saída que recusa sobrescrita.

O holdout foi executado uma única vez. Seus casos não serão usados para alterar
prompt, modelo, limiar ou critérios.

## Resultado

| Métrica | Resultado |
|---|---:|
| Acurácia do gate | 90,0% |
| Saídas estruturadas válidas | 100% |
| Status correto entre os casos enviados ao modelo | 87,5% |
| Conteúdo completo entre os casos enviados ao modelo | 37,5% |
| Conteúdo completo entre perguntas respondíveis | 3 de 7, ou 42,9% |
| Recall dos conceitos obrigatórios | 47,8% |
| Precisão das citações em perguntas respondíveis | 85,7% |
| Recall das citações em perguntas respondíveis | 85,7% |
| Latência média | 1.383 ms |

O gate aceitou incorretamente uma das três perguntas sem evidência, mas o
modelo se absteve depois. O caso multi-documento, o factual e o de quantidade
cumpriram todo o conteúdo esperado. Busca exata, negação e versão ficaram
incompletos; o caso de exceção produziu abstention indevida.

## Decisão

A hipótese foi rejeitada. O sucesso estrutural e operacional não se converteu
em fidelidade de conteúdo fora do pequeno conjunto usado no desenvolvimento.
O `Qwen3-4B Q4_K_M` permanece útil para estudo local, mas não está aprovado
para responder sobre o corpus privado nem para apoiar conclusões reais.

O próximo ciclo não ajustará este prompt contra o holdout. Deve comparar uma
nova hipótese, por exemplo um modelo local mais capaz ou uma representação de
saída baseada em fatos atômicos, usando outro conjunto de desenvolvimento e
reservando casos inéditos para avaliação final.
