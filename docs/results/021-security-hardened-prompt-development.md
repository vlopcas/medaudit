# Resultado 021: endurecimento do prompt contra instruções

## Hipótese e protocolo

Uma única instrução adicional poderia impedir que comandos presentes na
evidência contaminassem a resposta. A variante `security-hardened-v1` mantém a
política de resposta anterior e acrescenta que comandos, marcadores de papel e
objetos JSON na evidência são dados não confiáveis e não devem ser seguidos,
citados, parafraseados nem repetidos.

Modelo, dataset de segurança, schema, limite de 512 tokens, temperatura e três
repetições permaneceram fixos. Um teste automatizado confirma que a variante
altera somente a instrução. Foram executadas duas rodadas independentes,
totalizando 36 tentativas sobre o dataset de SHA-256
`824a01b2abd103f90022cd9f38973890d665b77d62993733f2293ab77c4e7dac`.

## Resultados

| Métrica | Rodada 1 | Rodada 2 | Combinado |
|---|---:|---:|---:|
| Estrutura, grounding e status | 100% | 100% | 100% (36/36) |
| Recall dos fatos requeridos | 100% | 100% | 100% |
| Conteúdo completamente correto | 83,3% | 83,3% | 83,3% (30/36) |
| Ausência de conceitos proibidos | 83,3% | 83,3% | 83,3% (30/36) |
| Maior latência | 3,88 s | 3,51 s | 3,88 s |
| Latência média | 3,02 s | 2,89 s | 2,96 s |

A variante corrigiu todas as tentativas com marcador falso de sistema e JSON
embutido, os dois formatos que falharam no baseline de segurança. Entretanto,
passou a repetir o valor proibido do override em inglês nas seis tentativas das
duas rodadas. Os demais formatos permaneceram corretos.

## Decisão

O prompt endurecido melhora a taxa agregada de 66,7% para 83,3%, mas é rejeitado
como solução de segurança suficiente. A falha apenas mudou de formato e foi
perfeitamente repetível. Continuar acrescentando exemplos ao prompt tenderia a
ajustar regras aos casos conhecidos sem estabelecer uma fronteira confiável.

A síntese permanece fora do runtime e do corpus privado. O próximo ciclo deve
implementar um gate determinístico e auditável antes da geração: evidências com
sinais explícitos de instrução devem bloquear síntese e seguir para revisão, sem
depender do modelo para ignorá-las. O detector será avaliado separadamente para
recall de ataques e falsos positivos em texto legítimo.

## Reprodução

```bash
docker compose run --rm benchmark-local-decomposed-grounding-security-hardened
```
