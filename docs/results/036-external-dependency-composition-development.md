# Resultado 036: composição de dependência externa em desenvolvimento

## Hipótese

Uma regra determinística que combine ação de consulta, origem externa e
necessidade de atualidade deve reduzir falsos negativos sem transformar menções
documentais estáticas em dependências externas. Sinais inequívocos, como dados
em tempo real, permanecem válidos diretamente.

## Mudança

O analisador passou a distinguir três grupos de sinais para formulações
genéricas:

- ação explícita de consulta;
- origem externa;
- necessidade de informação atual.

Os três grupos devem ocorrer juntos. A mudança não adiciona acesso externo: a
rota apenas interrompe retrieval e geração locais quando identifica que o
corpus não pode responder sozinho.

## Dataset e execução

O dataset público e integralmente sintético
`routed_compiled_external_development.json`, sob a política
`routed-compiled-integration-development-v1`, contém dez fluxos. Seu SHA-256 na
execução final foi
`fa9db7539110cfca416845050dfb7b7bbd7661c9fbf92107fae8bbf3731910ff`.

```bash
docker compose run --rm evaluate-routed-compiled-external-development
```

Ele cobre formulações compostas positivas, sinal externo inequívoco, menções
documentais estáticas, ausência de atualidade, ausência de origem e precedência
da decomposição. A primeira rodada revelou apenas um rótulo excessivo: a rota
de decomposição estava correta, mas a evidência era insuficiente para preparar
o request. O rótulo foi corrigido no conjunto de desenvolvimento sem alteração
do código.

## Resultado

- correspondência exata: 100% (10/10);
- segurança de emissão de request: 100% (10/10);
- todas as seis categorias atingiram 100%;
- quatro formulações compostas externas foram interrompidas antes do retrieval;
- os dois usos documentais estáticos permaneceram em recuperação direta;
- a suíte completa passou com 241 testes;
- Ruff passou sem achados e mypy passou em 166 arquivos.

## Decisão

A candidata está aprovada somente em desenvolvimento. O holdout do
[Resultado 035](035-routed-compiled-integration-holdout.md) permanece congelado
e não é reinterpretado. O próximo marco é criar e congelar outro holdout
sintético com formulações inéditas e controles negativos novos.

Nenhum acesso externo, cliente de LLM, modelo local ou corpus privado foi
habilitado.
