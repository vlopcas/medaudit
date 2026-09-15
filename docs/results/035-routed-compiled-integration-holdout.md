# Resultado 035: holdout da integração roteador-gateway

## Hipótese

A integração congelada deveria manter 100% de correspondência exata e emitir
um `LLMRequest` se, e somente se, a preparação terminasse em `prepared`, mesmo
em combinações temporais, clarificação, budget e bypass do gateway.

## Protocolo

O holdout contém seis casos integralmente sintéticos e inéditos sob a política
`routed-compiled-integration-holdout-v1`. O dataset foi congelado no commit
`3c22b85` com SHA-256
`85fe476a3995ca3cf30310b72d116d337bdeb30c28403aee489895f2123eb8c8`.
Antes da abertura, a imagem foi reconstruída e a suíte passou com 239 testes,
Ruff sem achados e mypy sem problemas em 166 arquivos.

O holdout foi executado uma única vez, sem rede e com filesystem somente
leitura. O relatório local foi gravado em
`artifacts/routed-compiled-integration-holdout.local.json`; o serviço recusa
sobrescrevê-lo.

```bash
docker compose run --rm evaluate-routed-compiled-integration-holdout
```

## Resultado

- correspondência exata: 83,3% (5/6);
- segurança de emissão de request: 100% (6/6);
- decomposição temporal preparada, clarificação, budget, rota direta e gateway
  desabilitado corresponderam ao esperado;
- o caso de dependência externa foi classificado como `direct_retrieval`, em vez
  de `requires_external_data`;
- apesar do erro de rota, esse caso não atravessou o gateway e não produziu
  request.

## Análise do erro

A consulta inédita combinava a ideia de fonte externa com atualização, mas o
analisador reconhece apenas um conjunto mais estreito de marcadores de origem.
Assim, a composição semântica desejada não foi detectada. Esse é um falso
negativo de roteamento e não uma falha da regra de emissão do gateway.

O caso e seu resultado permanecem congelados. Eles não serão reutilizados para
acrescentar um termo à heurística nem para recalcular a métrica.

## Decisão

A hipótese integrada foi rejeitada por não atingir correspondência exata total.
A segurança estrutural do gateway permaneceu intacta, mas isso não autoriza
síntese, modelo local, corpus privado ou alteração do runtime padrão.

O próximo ciclo deve criar um conjunto de desenvolvimento separado para tratar
dependências externas por uma regra composicional de origem e atualidade, em
vez de memorizar a frase do holdout. Depois de validação em desenvolvimento,
uma nova candidata exigirá outro holdout sintético inédito.
