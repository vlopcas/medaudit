# ADR-022: composição opt-in da aplicação de síntese

## Contexto

Pipeline, gateway e orquestrador possuíam contratos separados e avaliados, mas
o consumidor ainda precisava encadear manualmente preparação e síntese. Uma
composição incorreta poderia ignorar o resultado roteado ou entregar ao
orquestrador um objeto diferente daquele produzido para a consulta.

## Decisão

Introduzir `GroundedSynthesisApplication` como uma camada fina de aplicação:

- executa `retrieve_with_compiled_request` sem alterar sua API;
- encaminha o mesmo resultado ao `GroundedSynthesisOrchestrator`;
- preserva juntos a decisão roteada e o resultado de síntese;
- aceita IDs de revisão e `top_k` sem reinterpretá-los;
- usa um orquestrador desabilitado quando nenhum é injetado;
- não instancia cliente, modelo ou adaptador por conta própria.

## Consequências

O caminho completo pode ser exercitado por uma única operação assíncrona sem
ativar síntese por padrão. As políticas permanecem nas fronteiras já avaliadas:
o pipeline decide rota e evidência, o gateway prepara o request e o
orquestrador controla invocação e validação da saída.

Esta composição não é um endpoint, não executa ações externas e não autoriza o
corpus privado. Uma configuração experimental ainda precisa fornecer
explicitamente gateway, orquestrador e cliente.

## Validação

O primeiro gate deve usar somente dados sintéticos e clientes falsos, cobrindo
modo padrão, resposta validada, rotas sem preparação, clarificação e saída
inválida. Aprovação em desenvolvimento autoriza apenas um holdout inédito da
composição completa.

O holdout posterior atingiu 9/9 em correspondência, segurança de invocação e
segurança de liberação, incluindo temporalidade, revisão, budget, estados
desabilitados, saída inválida e timeout. A composição está aprovada como
arquitetura experimental com cliente falso. Essa decisão não promove modelo,
qualidade factual, endpoint, corpus privado ou ativação no runtime padrão.
