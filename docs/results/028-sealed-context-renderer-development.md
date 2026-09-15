# Resultado 028: renderer de contexto selado em desenvolvimento

## Hipótese

Uma serialização canônica coberta por SHA-256 deve detectar qualquer alteração
nos campos representados entre compilação e renderização, enquanto invariantes
explícitas continuam protegendo a topologia do contexto.

## Dataset e execução

O dataset público e integralmente sintético
`sealed_context_renderer_development.json`, política
`sealed-context-renderer-development-v1`, contém um controle válido e vinte
mutações. Elas cobrem o próprio selo, conteúdo, inventário, budget, confiança,
membership, duplicação, ordem, provenance, metadados de grupo e exclusões.

O SHA-256 do dataset executado foi
`993432ed15ce5982c5a76378dc0b2468742f47de26d0d3c5b1b4af964112af32`.
A imagem Docker foi reconstruída antes da execução, sem rede no serviço de
avaliação:

```bash
docker compose run --rm evaluate-sealed-context-security
```

## Resultado

- correspondência exata: 100% (21/21);
- controle íntegro aceito: 1/1;
- mutações inseguras recusadas: 100% (20/20);
- correspondência exata em cada uma das onze categorias: 100%.

A suíte completa executada na mesma imagem passou com 225 testes; Ruff e mypy
também passaram, com 160 arquivos analisados pelo mypy.

## Decisão

A candidata está aprovada somente no desenvolvimento. O resultado demonstra
cobertura sobre as mutações conhecidas, não generalização. O renderer continua
opt-in e fora do runtime, e modelo local e corpus privado não participaram do
experimento.

O próximo gate é um novo holdout sintético e congelado, criado sem reutilizar
estes casos como conjunto de ajuste. O SHA-256 sem chave segue sendo um detector
de alteração interna, não autenticação contra um agente capaz de recalculá-lo.
