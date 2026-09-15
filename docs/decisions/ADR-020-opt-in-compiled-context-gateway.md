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

O desenvolvimento atingiu 5/5 e o holdout congelado posterior também atingiu
5/5, ambos com 100% na correspondência entre status e presença de request. O
gateway está, portanto, autorizado a ser uma dependência opcional do roteador;
o modo padrão continua `disabled` e esta decisão não inclui chamada de modelo.

A conexão usa o método separado `retrieve_with_compiled_request`. Ele preserva
`retrieve` sem mudanças e só chama o gateway quando uma rota de decomposição
possui execução e bundle. Rotas diretas, externas ou sem executor não atravessam
essa fronteira. O resultado composto mantém decisão de retrieval e preparação
distintas; nenhuma resposta generativa é produzida.

A avaliação integrada em desenvolvimento atingiu 7/7 em correspondência e
segurança de emissão de request. Isso autoriza somente um holdout da unidade
roteador-gateway; a conexão permanece experimental e sem cliente de LLM.

O holdout integrado posterior manteve 6/6 na segurança de emissão, mas atingiu
5/6 na correspondência exata. Uma formulação inédita de dependência externa foi
classificada como recuperação direta. Portanto, a unidade integrada não foi
promovida. O holdout permanece congelado; qualquer nova candidata deve ser
desenvolvida em dados separados e enfrentar outro holdout inédito.

No ciclo de desenvolvimento separado, marcadores externos genéricos passaram a
exigir conjuntamente ação de consulta, origem externa e atualidade. A candidata
atingiu 10/10 em correspondência e segurança de emissão, inclusive diante de
menções documentais estáticas. Isso autoriza apenas um novo holdout sintético;
não altera o resultado nem os dados do holdout anterior.
