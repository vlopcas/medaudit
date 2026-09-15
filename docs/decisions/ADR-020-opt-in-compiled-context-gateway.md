# ADR-020: gateway opt-in para contexto compilado

## Contexto

O compilador e o renderer de contexto selado passaram pelos gates sintéticos,
mas o pipeline terminava no pacote de evidências agrupadas. Faltava uma
fronteira explícita para conectá-los sem ativar geração, registrar conteúdo ou
alterar o comportamento padrão.

## Opções consideradas

1. Substituir diretamente o construtor anterior no caminho padrão.
2. Controlar a integração por uma variável booleana dispersa no pipeline.
3. Introduzir um gateway tipado, desabilitado por padrão e sem cliente de LLM.

## Decisão

Adotar a terceira opção. `CompiledContextGateway`:

- inicia em modo `disabled` e só compila em modo explícito `experimental`;
- recebe um `DecompositionEvidenceBundle` já produzido pelo pipeline;
- compila, verifica e renderiza o contexto sem invocar qualquer modelo;
- nunca retorna um request quando compilação, budget ou renderização falham;
- converte falhas esperadas em códigos genéricos, sem propagar detalhes que
  possam conter consulta ou evidência;
- retorna telemetria com modo, status, estado do contexto, código de falha,
  contagens, budget, tokens estimados e duração;
- não inclui texto, IDs de evidência, documentos, consultas ou hashes nessa
  telemetria.

## Consequências

O caminho experimental pode ser exercitado sem alterar o runtime padrão e sem
acoplar o compilador a um provider. A ausência de `LLMClient` no gateway impede
que ativá-lo, por si só, envie dados ou gere respostas.

Falha fechada aqui significa ausência de `LLMRequest`; não significa que todos
os erros de infraestrutura sejam recuperáveis. Exceções esperadas de contrato
são reduzidas a códigos seguros, enquanto falhas inesperadas continuam visíveis
para diagnóstico no limite da aplicação, onde também não devem ser registradas
com payloads sensíveis.

## Como validar

- comprovar que o modo padrão não compila nem produz request;
- comprovar equivalência do request no modo experimental;
- bloquear budget insuficiente e erros esperados do compilador;
- verificar que a telemetria não contém texto nem identificadores;
- manter qualquer chamada de modelo fora deste componente;
- avaliar o gateway antes de conectá-lo ao roteador principal.
