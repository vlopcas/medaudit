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
