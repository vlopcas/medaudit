# Resultado 037: segundo holdout da integração roteador-gateway

## Hipótese

A candidata composicional deveria atingir 100% de correspondência de rota e
preservar a regra de que um `LLMRequest` existe se, e somente se, a preparação
termina em `prepared`, diante de formulações externas e controles negativos
inéditos.

## Protocolo

O holdout contém dez casos integralmente sintéticos sob a política
`routed-compiled-integration-holdout-v2`. Dataset, código e configuração foram
congelados no commit `ce52a35`, antes da execução, com SHA-256
`b0e7168b233eefad27362b71c2e8ff8e1f2c3ad8b6c0158132b6708b1b1a0ee8`.

A pré-validação reconstruiu as imagens e passou com 241 testes, Ruff sem achados
e mypy sem problemas em 166 arquivos. O holdout foi então executado uma única
vez, sem rede e com filesystem da aplicação somente leitura. O relatório local
foi gravado em
`artifacts/routed-compiled-integration-holdout-v2.local.json`, com recusa de
sobrescrita.

```bash
docker compose run --rm evaluate-routed-compiled-integration-holdout-v2
```

## Resultado

- correspondência exata: 100% (10/10);
- segurança de emissão de request: 100% (10/10);
- todas as seis categorias atingiram 100%;
- as quatro dependências externas compostas pararam antes do retrieval;
- a dependência externa teve precedência sobre a comparação;
- menções documentais estáticas, origem sem atualidade e atualidade sem origem
  não foram classificadas como dependência externa;
- uma comparação sem ação externa seguiu para decomposição e falhou fechada por
  evidência insuficiente, sem request.

## Decisão

A integração entre roteador, executor, agrupamento e gateway está aprovada como
fronteira estrutural experimental e opt-in. O modo padrão continua desabilitado
e nenhuma ação externa é executada pela rota.

Esta aprovação não promove o modelo local, não autoriza corpus privado e não
ativa síntese no runtime. O próximo marco é definir uma camada isolada de
orquestração que receba somente requests preparados, use um cliente injetável e
submeta toda saída ao validador determinístico. O primeiro ciclo deve usar
apenas cliente falso e casos sintéticos, permanecendo desabilitado por padrão.
