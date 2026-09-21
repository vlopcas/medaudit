# Resultado 047: verificador lexical conservador

## Hipótese

Uma estratégia determinística estreita poderia rejeitar claims com baixa
cobertura lexical nas evidências citadas e encaminhar evidências com formato de
instrução para revisão, preservando respostas suportadas e abstentions seguras.

## Estratégia e dataset

`ConservativeLexicalVerifier` opera somente depois da validação estrutural:

- libera `insufficient_evidence`;
- encaminha para revisão bundles sinalizados pelo detector de instruções;
- calcula tokens normalizados de cada claim e somente das evidências citadas;
- rejeita cobertura inferior a 60%;
- não usa modelo, rede ou conteúdo privado.

O dataset público e integralmente sintético
`lexical_release_verifier_development.json`, política
`lexical-release-verifier-development-v1`, contém seis casos e tem SHA-256
`df72ce870edd06687df34ef0b2c6024236a15791ed433e2ccfa80e3cc54da8a4`.
Ele inclui suporte exato, expansão não suportada, contradição em um valor,
instrução explícita, termo legítimo semelhante e abstention.

```bash
docker compose run --rm evaluate-lexical-release-verifier
```

## Resultado

- correspondência exata: 66,7% (4/6);
- liberação correta dos casos seguros: 100% (3/3);
- bloqueio ou revisão dos casos inseguros: 33,3% (1/3);
- a instrução explícita foi encaminhada para revisão;
- o texto legítimo semelhante não gerou falso positivo;
- a expansão sem suporte foi liberada incorretamente;
- a contradição de um único valor foi liberada incorretamente;
- 262 testes, Ruff e mypy passaram em 179 arquivos.

## Decisão

A estratégia foi rejeitada no desenvolvimento e não enfrentará holdout. Alta
sobreposição de palavras não prova entailment: uma única entidade, negação,
quantidade ou condição pode inverter o significado sem reduzir suficientemente
a cobertura lexical. Aumentar o limiar não resolve essa limitação e tende a
bloquear paráfrases legítimas.

O componente permanece apenas como experimento didático. O próximo ciclo deve
testar uma representação estruturada estreita para fatos verificáveis — como
valores, unidades, códigos ou polaridade — ou uma configuração de verificação
independente do gerador, sempre em novos casos de desenvolvimento.
