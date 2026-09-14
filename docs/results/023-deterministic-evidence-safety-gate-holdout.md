# Resultado 023: holdout do gate determinístico de segurança

## Hipótese e protocolo

O gate `evidence-instruction-safety-v1`, aprovado no desenvolvimento, deveria
generalizar para ataques parafraseados e formatos limítrofes sem bloquear texto
legítimo semelhante. O holdout integralmente sintético foi congelado antes da
execução no commit `f6b8664`, com SHA-256
`d69bb54b57988bcdab03941779487a6a309fee18166e057641dff4a22919027a`.

O conjunto contém oito ataques e oito controles legítimos inéditos. O comando
exige o hash congelado e recusa sobrescrever o relatório local, impedindo que
uma repetição silenciosa substitua a primeira observação.

## Resultados

| Métrica | Desenvolvimento | Holdout |
|---|---:|---:|
| Correspondência exata dos sinais | 100% | 68,75% (11/16) |
| Recall dos ataques | 100% | 50% (4/8) |
| Especificidade nos textos legítimos | 100% | 87,5% (7/8) |
| Decisão correta de quarentena | 100% | 68,75% (11/16) |

Quatro ataques não foram detectados: override parafraseado em português,
override parafraseado em inglês, manipulação de citação parafraseada e um
marcador de papel no formato de token especial. Um texto técnico legítimo com a
palavra `output` gerou o único falso positivo. O relatório permaneceu limitado
a IDs, categorias, contagens e resultados; nenhum texto de evidência foi
materializado nele.

## Decisão

O gate foi rejeitado para integração ao runtime. Expressões regulares enumerando
formas conhecidas não estabelecem uma fronteira de segurança generalizável e
podem simultaneamente perder paráfrases e bloquear vocabulário legítimo. O
resultado de desenvolvimento não deve ser usado como justificativa para
promoção.

Este holdout permanece congelado e não será usado para acrescentar padrões ao
detector. Um novo ciclo de desenvolvimento deverá formular uma arquitetura de
defesa em profundidade, com separação estrutural do contexto, política de
quarentena conservadora e avaliação própria. Qualquer candidata futura exigirá
outro holdout inédito antes de alcançar o runtime ou o corpus privado.

## Reprodução

A primeira execução já materializou o relatório local protegido. Reexecutar o
comando abaixo deve falhar em vez de sobrescrevê-lo:

```bash
docker compose run --rm evaluate-evidence-safety-holdout
```
