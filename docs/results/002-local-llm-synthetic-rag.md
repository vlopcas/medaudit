# Resultado 002: RAG sintético com LLM local

## Hipótese

Um modelo generativo local de 4B quantizado consegue respeitar o contrato JSON,
citar apenas evidências autorizadas e executar dentro dos 8 GiB de VRAM antes
de qualquer teste com o corpus privado.

## Configuração

- dataset público integralmente sintético: 7 casos;
- retriever: BM25, `top_k` 3;
- gate sintético: score máximo maior ou igual a 3;
- modelo: `Qwen/Qwen3-4B-GGUF`, `Q4_K_M`;
- runtime: `llama.cpp` CUDA, build `b10335`, imagem fixada por digest;
- contexto: 8.192 tokens, uma execução paralela e todas as camadas na GPU;
- geração: temperatura zero e saída restringida por JSON Schema.

O limiar 3 pertence somente ao pequeno dataset sintético e não substitui a
política calibrada do corpus privado.

## Resultado

| Métrica | Resultado |
|---|---:|
| Acurácia do gate | 100% |
| Casos enviados ao modelo | 6 de 7 |
| Saídas estruturadas válidas | 100% |
| Gerações com ao menos uma citação relevante | 100% |
| Latência média por geração | 3.454 ms |
| VRAM observada com o servidor carregado | 3.765 MiB |

O runtime produziu aproximadamente 76–79 tokens por segundo nas requisições
observadas. O relatório local contém apenas essas métricas agregadas; textos
gerados não foram persistidos.

## Interpretação

A hipótese operacional foi confirmada: modelo e runtime cabem com folga na GPU
e o caminho estruturado funciona ponta a ponta. Isso ainda não mede exatidão da
resposta, suporte de cada afirmação pela passagem, robustez adversarial nem
qualidade sobre documentos reais.

O modelo permanece candidato. O próximo experimento deve acrescentar respostas
esperadas sintéticas e avaliação determinística de conteúdo antes de autorizar
o uso do pipeline generativo com o corpus privado.
