# Resultado 034: integração roteador-gateway em desenvolvimento

## Hipótese

A operação composta deve produzir um `LLMRequest` somente quando a rota exigir
decomposição, o executor produzir um bundle suficiente e o gateway estiver em
modo experimental sem bloqueios. Todas as demais rotas e estados devem terminar
sem request.

## Dataset e execução

O dataset público e integralmente sintético
`routed_compiled_integration_development.json`, política
`routed-compiled-integration-development-v1`, contém sete fluxos. Seu SHA-256 na
execução foi
`4cd5c8cc40a28c1e8d1807fdc9ec8e3d19f97ddc32404f6a673a63ef5026c265`.

```bash
docker compose run --rm evaluate-routed-compiled-integration
```

O serviço executou sem rede e com filesystem somente leitura.

## Resultado

- correspondência exata: 100% (7/7);
- segurança de emissão de request: 100% (7/7);
- todas as sete categorias atingiram 100%;
- apenas decomposição executada, suficiente e experimental produziu request;
- rotas direta e externa, ausência de executor, gateway desabilitado,
  retrieval insuficiente e revisão terminaram sem request.

O teste do avaliador confirmou que seu relatório omite consulta e
identificadores de chunk e documento. A suíte reconstruída passou com 239
testes; Ruff e mypy também passaram, com 166 arquivos analisados pelo mypy.

## Decisão

A integração está aprovada somente no desenvolvimento e pode avançar para um
holdout sintético inédito. O método continua opt-in, o gateway permanece
desabilitado por padrão e nenhum cliente de LLM participa do fluxo.

O próximo holdout deve desafiar combinações temporais, clarificação, budgets e
evidência compartilhada sem reutilizar estes casos. Modelo local, corpus privado
e automação decisória permanecem bloqueados.
