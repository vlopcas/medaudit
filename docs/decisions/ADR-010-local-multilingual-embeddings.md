# ADR-010: Embeddings multilíngues locais e reproduzíveis

## Status

Aceita em 2026-09-11.

## Contexto

A busca híbrida requer um retriever semântico, mas o corpus é privado e não
pode ser enviado implicitamente a APIs. O ambiente disponível possui GPU NVIDIA
com 8 GiB de VRAM, enquanto o WSL dispõe de menos memória que o host.

O modelo precisa compreender português, caber nesse ambiente e possuir um modo
de uso simples o suficiente para isolar download e inferência.

## Decisão

Usar inicialmente `intfloat/multilingual-e5-base`, fixado por hash de revisão.
Consultas recebem o prefixo `query:` e chunks recebem `passage:`. Os vetores são
normalizados antes da similaridade.

O extra Python `semantic` não faz parte da imagem padrão de desenvolvimento.
Um serviço Docker com rede, sem montagem de `data/`, baixa e verifica o modelo
em `models/`. Outro serviço monta esse cache como somente leitura e funciona
sem rede. O diretório de modelos e seu manifesto local são ignorados pelo Git.

A imagem semântica possui Dockerfile próprio: a camada grande de PyTorch e
Sentence Transformers é instalada antes da cópia do código. Mudanças comuns no
projeto reutilizam essa camada. O índice denso trabalha com matrizes `float32`
normalizadas e similaridade por produto interno, equivalente ao cosseno.
Embeddings de chunks são persistidos em um artefato local incremental. A chave
é o ID do chunk, acompanhada do hash do texto; colisões de conteúdo e mudanças
de modelo ou revisão interrompem o processo em vez de reutilizar vetores
obsoletos.

Um profiler offline usa o tokenizer real, com prefixo e tokens especiais, para
medir a distribuição e a taxa de chunks truncados sem registrar texto. Mudanças
de chunking motivadas por limite de contexto dependem dessa medição.

O experimento de mitigação preserva os chunks e a proveniência originais. Apenas
passagens acima da capacidade são divididas em janelas de tokens com sobreposição
de 64 tokens; os vetores normalizados das janelas são promediados e normalizados
novamente. A estratégia integra a identidade do cache, impedindo reutilização
acidental dos vetores truncados.

## Consequências

- documentos privados nunca são necessários durante o download;
- a revisão fixada torna o experimento repetível;
- a imagem semântica e o cache ocupam espaço considerável;
- a inferência pode usar GPU, com CPU como possibilidade futura;
- trocar o modelo exige novo experimento somente na calibração.

## Como validar

- confirmar acesso à GPU dentro do container;
- baixar o modelo sem montar o corpus;
- recarregar o mesmo hash com rede desabilitada;
- verificar dimensão e normalização com textos sintéticos;
- nunca registrar textos ou vetores privados no terminal.
