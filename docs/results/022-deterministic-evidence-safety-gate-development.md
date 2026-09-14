# Resultado 022: gate determinístico de segurança da evidência

## Hipótese e protocolo

Sinais explícitos de instrução dentro da evidência podem ser identificados antes
da geração sem depender do LLM. O gate `evidence-instruction-safety-v1` é
provider-neutral, recebe um pacote de evidências e retorna somente IDs e códigos
de sinal. Ele não devolve o texto analisado e ainda não está conectado ao
runtime.

O conjunto de desenvolvimento é integralmente sintético e balanceado: seis
ataques explícitos e seis textos legítimos com termos semelhantes. Ele cobre
marcadores falsos de papel, overrides em português e inglês, JSON com formato de
resposta e manipulação de citações. A especificidade é medida contra referências
legítimas a sistema, regras de campos ignorados, status, JSON, prazo de resposta
e `evidence_id`. O SHA-256 do dataset é
`346394031508dd311f62079d707b625cea94c9db7d787881ec861f84b65fe591`.

## Resultados

| Métrica | Resultado |
|---|---:|
| Correspondência exata dos sinais | 100% (12/12) |
| Recall dos ataques | 100% (6/6) |
| Especificidade nos textos legítimos | 100% (6/6) |
| Decisão correta de quarentena | 100% (12/12) |

Os relatórios por caso contêm somente identificador, categoria, resultado e
quantidade de sinais. Testes unitários também confirmam que achados e avaliações
não incluem o conteúdo da evidência.

## Decisão

O componente é mantido como candidato isolado. O resultado demonstra o contrato
e o comportamento nos padrões conhecidos, mas não prova segurança geral:
expressões novas ainda podem gerar falsos negativos e textos legítimos fora do
conjunto podem gerar falsos positivos. O gate é uma barreira de quarentena, não
um sanitizador.

Antes de integrar ao runtime, o próximo ciclo deve congelar um holdout sintético
inédito, cobrir paráfrases e casos limítrofes adicionais e verificar que o gate
continua emitindo apenas metadados auditáveis. Evidência sinalizada deverá seguir
para revisão, nunca ser silenciosamente modificada.

## Reprodução

```bash
docker compose run --rm evaluate-evidence-safety
```
