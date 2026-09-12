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

## Avaliação de conteúdo

Os seis casos respondíveis receberam respostas esperadas e grupos de conceitos
obrigatórios, com alternativas lexicais explícitas. A comparação normaliza
caixa, acentos e pontuação, não utiliza outro LLM como juiz e não persiste as
respostas geradas.

| Variante | Conteúdo completo | Status | Citação relevante | Latência média |
|---|---:|---:|---:|---:|
| Prompt inicial, `top_k=3` | 50,0% | 83,3% | 83,3% | 3.084 ms |
| Prompt inicial, `top_k=1` | 33,3% | 83,3% | 83,3% | 2.880 ms |
| Prompt explícito e `/no_think`, `top_k=3` | 66,7% | 100% | 100% | 1.159 ms |

A redução isolada do contexto foi rejeitada. Explicitar no prompt o formato que
o JSON Schema restringe e desativar o raciocínio oculto melhorou formato,
citações, conteúdo e latência. Mesmo assim, um caso de busca exata e um factual
continuaram incompletos.

O conjunto possui somente seis perguntas respondíveis e já orientou mudanças
de prompt. Ajustá-lo novamente seria overfitting. O modelo não está aprovado
para geração sobre o corpus privado; o próximo gate requer novos casos
sintéticos mantidos fora desse ciclo de desenvolvimento.
