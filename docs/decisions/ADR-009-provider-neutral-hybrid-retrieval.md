# ADR-009: Busca híbrida independente de fornecedor

## Status

Aceita em 2026-09-11.

## Contexto

A baseline lexical recuperou todas as referências dos casos respondíveis no
holdout, mas o limiar de confiança ainda aceitou parte relevante das perguntas
sem evidência. O próximo experimento deve estudar recuperação semântica sem
acoplar domínio, avaliação ou proveniência a uma biblioteca de embeddings.

Scores de BM25 e similaridade vetorial possuem escalas distintas. Somá-los
diretamente exigiria normalização sensível ao corpus e tornaria a comparação
menos interpretável.

## Decisão

Retrievers implementam um contrato mínimo de busca e retornam o mesmo modelo de
resultado com chunk e score. A combinação inicial usa Reciprocal Rank Fusion
(RRF), que considera posições em vez dos scores brutos.

O RRF é determinístico, aceita pesos positivos, usa desempate estável por ID do
chunk e busca uma profundidade de candidatos explícita. O adaptador denso e o
modelo local serão decisões separadas; nenhum documento será enviado a serviço
externo implicitamente.

O desenvolvimento e a escolha de parâmetros usam somente a partição de
calibração. O holdout já aberto fica registrado como resultado da baseline e
não será reutilizado para selecionar a busca híbrida.

O primeiro benchmark compara BM25, dense e RRF com pesos iguais, constante 60,
profundidade de candidatos 20 e `top_k` 5. O comando é deliberadamente restrito
à calibração e valida o manifesto de split antes de executar qualquer consulta.
Pesos e profundidade podem ser variados em experimentos de calibração, desde
que cada variante seja gravada em artefato local separado.

Uma quarta alternativa mantém o BM25 como gerador de candidatos e aplica a
evidência semântica somente para reordenar esse conjunto. A combinação também
usa posições, preserva o universo lexical de candidatos e nunca introduz um
chunk que o BM25 não tenha recuperado.

## Consequências

- BM25 continua sendo a baseline transparente;
- o backend semântico pode ser substituído sem alterar a fusão;
- pesos e profundidade precisam ser registrados por experimento;
- a qualidade semântica depende do modelo local que ainda será escolhido;
- uma comparação final imparcial exigirá novos casos mantidos fora da
  calibração.

## Como validar

- provar que rankings com escalas incompatíveis são fundidos corretamente;
- validar pesos, limites e desempates determinísticos;
- rejeitar retrievers que discordem sobre a identidade do mesmo chunk;
- usar somente dados sintéticos nos testes versionados.
