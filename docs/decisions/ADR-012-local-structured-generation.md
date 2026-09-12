# ADR-012: geração estruturada com modelo local

## Status

Aceita em 2026-09-12.

## Contexto

O contrato de RAG já impede geração sem evidência aceita e valida as citações
retornadas. Falta um adaptador concreto que preserve a privacidade do corpus,
caiba na GPU disponível e gere o JSON exigido pelo contrato.

## Decisão

O primeiro candidato será o modelo oficial `Qwen/Qwen3-4B-GGUF`, revisão
`3b6d9922d71c6d316a0c9de39a95fbe8594b9a0b`, arquivo
`Qwen3-4B-Q4_K_M.gguf`. A quantização e o tamanho são uma escolha inicial para
o ambiente com 8 GiB de VRAM, não uma promoção de qualidade.

O runtime será `llama.cpp`, que oferece servidor compatível com chat
completions e geração restringida por JSON Schema. O adaptador usa apenas a
biblioteca padrão do Python, não registra prompts ou respostas e aceita por
padrão somente HTTP em loopback. Endpoints externos e HTTPS são recusados para
evitar envio acidental das evidências privadas.

O download do modelo será uma operação isolada, sem montagem de `data/`. A
primeira execução end-to-end usará exclusivamente o corpus sintético
versionado. Uso com documentos privados somente será habilitado depois de
medir formato válido, citações, abstention, latência e uso de memória nesse
ensaio.

## Consequências

- não há dependência de API externa durante inferência;
- modelo, revisão e arquivo ficam explícitos no código;
- JSON Schema reduz saídas malformadas, mas não prova correção factual;
- o artefato GGUF permanece local e ignorado pelo Git;
- trocar quantização, modelo ou runtime exige novo resultado comparável.

## Como validar

- testar o adaptador com transporte sintético e sem rede;
- recusar URLs que não sejam loopback;
- confirmar que o schema é enviado ao runtime;
- rejeitar conteúdo que não seja um objeto JSON;
- executar posteriormente o benchmark sintético na GPU antes do corpus real.
