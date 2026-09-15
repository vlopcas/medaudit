# Resultado 032: gateway de contexto compilado em desenvolvimento

## Hipótese

O gateway opt-in deve permanecer inerte quando desabilitado, produzir um
`LLMRequest` somente após preparação válida e falhar fechado diante de budget,
revisão ou erro esperado do compilador. O relatório e a telemetria não podem
reter consultas, evidências ou identificadores.

## Dataset e execução

O dataset público e integralmente sintético
`compiled_context_gateway_development.json`, política
`compiled-context-gateway-development-v1`, contém cinco casos. Seu SHA-256 na
execução foi
`7dd7819d182e4126c260ec11621aec95fbe081ae643a3ed30f5df04ca2ce197f`.

```bash
docker compose run --rm evaluate-compiled-context-gateway
```

O serviço foi executado sem rede e com filesystem somente leitura.

## Resultado

- correspondência exata: 100% (5/5);
- segurança de emissão de request: 100% (5/5);
- modo desabilitado: nenhum request;
- preparação válida: request presente;
- budget insuficiente, revisão e rejeição do compilador: nenhum request;
- todas as cinco categorias atingiram 100%.

O teste automatizado do relatório confirmou ausência dos marcadores sintéticos
de consulta, conteúdo, ID de evidência e documento. A suíte reconstruída passou
com 234 testes; Ruff e mypy também passaram, com 164 arquivos analisados pelo
mypy.

## Decisão

O gateway está aprovado somente no desenvolvimento. Ele permanece desconectado
do `RoutedEvidenceFirstPipeline` e não possui cliente de LLM. O próximo gate é
um holdout sintético inédito com combinações de bloqueios, contagens e garantia
de que request e telemetria nunca divergem.

Modelo local, corpus privado, runtime padrão e automação decisória permanecem
fora desta promoção.
