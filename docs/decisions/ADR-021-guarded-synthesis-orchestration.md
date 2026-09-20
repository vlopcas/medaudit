# ADR-021: orquestração de síntese com liberação validada

## Contexto

O roteador e o gateway compilado passaram pelo segundo holdout integrado, mas o
pipeline ainda terminava em um `LLMRequest`. Conectar diretamente esse request
a um cliente permitiria que respostas brutas ou não grounded escapassem para o
consumidor e confundiria preparação, inferência e validação numa única etapa.

## Decisão

Introduzir `GroundedSynthesisOrchestrator` como fronteira separada e opt-in:

- o modo padrão `disabled` nunca chama o cliente;
- o modo `experimental` exige um `LLMClient` injetado;
- somente um request previamente preparado pelo gateway pode chegar ao cliente;
- a resposta bruta permanece interna à fronteira;
- toda resposta passa pelo validador determinístico ligado ao bundle original;
- apenas `DecomposedGroundedAnswer` validado pode ser devolvido;
- falhas de cliente ou validação terminam sem resposta;
- a telemetria omite consulta, prompt, evidências, resposta, modelo e IDs.

## Consequências

A implementação não ativa o `LlamaCppClient`, não altera o runtime padrão e não
autoriza uso do corpus privado. Ela permite testar separadamente se o cliente é
chamado apenas quando permitido e se nenhuma saída não validada atravessa a
fronteira.

Falhas operacionais esperadas do adaptador são reduzidas ao código genérico
`client_failed`. Violações do contrato grounded produzem `response_rejected`.
Erros de programação não previstos continuam fora dessa conversão.

## Validação

O primeiro ciclo usa exclusivamente clientes falsos e dados sintéticos. Para
avançar, deve comprovar modo desabilitado, ausência de chamada sem request
preparado, resposta e abstention válidas, rejeição de citação fora do grupo e
falha fechada do cliente. Um resultado em desenvolvimento não autoriza modelo
real; exige holdout sintético inédito.
