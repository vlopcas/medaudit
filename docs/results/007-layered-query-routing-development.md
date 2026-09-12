# Resultado 007: roteamento de consultas em camadas

## Hipótese

Separar bloqueios conservadores do planejamento semântico deveria produzir uma
decisão de rota mais segura que exigir todos os campos de uma única
classificação. Dependência externa permanece determinística; decomposição usa a
união entre sinais determinísticos e o parecer do LLM; intenção não controla a
rota.

## Configuração

- os mesmos 16 casos sintéticos de desenvolvimento do Resultado 006;
- três rotas: retrieval direto, decomposição e dependência externa;
- precedência explícita para dependência externa;
- indicação externa do LLM ignorada pela política de bloqueio;
- decomposição aceita quando qualquer uma das duas análises a solicita;
- nenhuma integração com retrieval e nenhum novo holdout.

## Resultado

| Métrica | Resultado |
|---|---:|
| Acurácia da rota | 87,5% (14/16) |
| Bloqueios externos indevidos | 0% |
| Latência média do modelo | 347 ms |

Os dois erros restantes foram falsos negativos de decomposição em formulações
multi-documento. Nenhuma pergunta local foi bloqueada como dependência externa.

## Decisão

A separação de responsabilidades foi mantida como candidata, mas ainda não foi
promovida. Acurácia de 87,5% no desenvolvimento não justifica abrir um holdout
nem alterar o RAG.

O próximo experimento deve detectar estrutura multi-documento sem depender de
uma lista crescente de verbos. Ele precisa incluir novos casos negativos com
termos no plural para medir falsos positivos antes de qualquer avaliação final.

