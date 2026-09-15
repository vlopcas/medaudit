# Resultado 033: holdout do gateway de contexto compilado

## Hipótese e protocolo

O gateway aprovado no desenvolvimento deveria manter a correspondência entre
status e emissão de request em combinações inéditas: curto-circuito desabilitado,
bundle incompleto, múltiplas revisões, evidência compartilhada e revisão dessa
evidência compartilhada.

O dataset integralmente sintético foi congelado antes da primeira execução no
commit `cc65840`, com SHA-256
`c8b43428fa6d14bfe37254c29cd2fd9e48c62082e7d60850dd1b2d021a264e34`.
O gateway não foi alterado após o congelamento. O serviço executou sem rede,
validou o hash e gravou um relatório local protegido contra sobrescrita:

```bash
docker compose run --rm evaluate-compiled-context-gateway-holdout
```

## Resultado

- correspondência exata: 100% (5/5);
- segurança de emissão de request: 100% (5/5);
- todas as cinco categorias atingiram 100%;
- somente a evidência compartilhada válida produziu request;
- modo desabilitado, bundle incompleto e ambos os cenários de revisão não
  produziram request.

O caso desabilitado recebeu um estimador que lançaria erro se fosse chamado,
confirmando o curto-circuito anterior à compilação. A evidência compartilhada
foi deduplicada em um item, preservada em dois grupos e registrada apenas por
contagens no relatório.

A suíte usada antes do congelamento passou com 234 testes; Ruff e mypy também
passaram, com 164 arquivos analisados pelo mypy.

## Decisão

O gateway está aprovado para ser injetado como dependência opcional no
`RoutedEvidenceFirstPipeline`, permanecendo desabilitado por padrão. A conexão
deve expor apenas o resultado do gateway para a rota de decomposição que possua
um bundle completo; nenhuma rota pode chamar modelo ou contornar seus gates.

Este resultado não aprova qualidade generativa, modelo local, corpus privado ou
automação decisória. Esses limites permanecem fora de escopo.
