# Resultado 069: identidade versionada da política de relações

## Hipótese

Vincular uma política de relações nomeada e versionada à admissão e à publicação
elimina a lacuna em que o mesmo conteúdo de grafo poderia representar decisões
de governança diferentes sem alterar a identidade do snapshot.

## Implementação e avaliação

`GraphRelationPolicy` exige nome, versão positiva e allowlist não vazia. Seu
identificador é o SHA-256 de uma serialização canônica com as relações ordenadas.
Esse identificador acompanha `GraphAdmissionResult`, integra
`PublishedGraphCatalog` e participa do hash da publicação.

Uma troca de política é reportada como
`relation-policy:<identificador-anterior>` e segue o mesmo protocolo de revisão
vinculada ao snapshot anterior usado para outras mudanças governadas.

O dataset sintético de publicação foi ampliado de dez para doze casos. Os dois
novos casos mantêm grafo e provenance constantes e alteram apenas a versão da
política: um deve permanecer em revisão e o outro deve publicar após revisão
corretamente vinculada.

```bash
docker compose build checks evaluate-graph-catalog-publication
docker compose run --rm checks
docker compose run --rm evaluate-graph-catalog-publication
```

## Resultado

- 12/12 casos da avaliação de publicação corresponderam ao esperado;
- a troca de política sem revisão permaneceu bloqueada em revisão;
- a mesma troca foi publicada após revisão vinculada ao snapshot anterior;
- a identidade da publicação mudou quando apenas a identidade da política
  mudou;
- 335 testes passaram;
- Ruff passou;
- mypy não encontrou problemas em 223 arquivos;
- SHA-256 observado do dataset de desenvolvimento:
  `d17138e114b19e7fa6dcfe24981a91533e63a4d91a5ce52b436c5e6edd8ed88e`.

## Decisão

A lacuna identificada no Resultado 068 foi fechada no escopo sintético de
desenvolvimento. A publicação completa está pronta para o próximo gate: criar,
revisar e congelar um holdout sintético inédito antes de executá-lo uma única
vez.

Persistência, concorrência, assinatura, extração e dados privados continuam fora
do escopo.

## Resultado posterior

O holdout congelado do
[Resultado 070](070-graph-catalog-publication-holdout.md) atingiu 8/8 e encerrou
esse gate sem reutilização para ajuste.
