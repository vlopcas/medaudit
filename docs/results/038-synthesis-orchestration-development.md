# Resultado 038: orquestração de síntese em desenvolvimento

## Hipótese

A camada de orquestração deve chamar um cliente somente quando recebe um request
preparado e deve liberar somente uma resposta que passe pelo validador grounded
determinístico.

## Dataset e execução

O dataset público e integralmente sintético
`synthesis_orchestration_development.json`, sob a política
`synthesis-orchestration-development-v1`, contém sete fluxos. Seu SHA-256 na
execução foi
`f9ed81c8c7c536ef5be5e06ad11b414addd676ba569ac9c82a1f7635edd629e3`.

```bash
docker compose run --rm evaluate-synthesis-orchestration
```

O serviço executou sem rede, com filesystem somente leitura e clientes falsos.
Nenhum servidor de inferência, modelo ou corpus privado participou.

## Resultado

- correspondência exata: 100% (7/7);
- segurança de liberação: 100% (7/7);
- todas as sete categorias atingiram 100%;
- modo desabilitado, ausência de request e gateway bloqueado não chamaram o
  cliente;
- resposta grounded e abstention válidas foram aceitas;
- citação cruzada foi rejeitada sem liberar resposta;
- falha sintética do cliente terminou sem resposta;
- a suíte completa passou com 247 testes;
- Ruff passou sem achados e mypy passou em 169 arquivos.

## Decisão

A orquestração está aprovada somente em desenvolvimento com cliente falso. Ela
permanece desabilitada por padrão e ainda não está incorporada como chamada
automática do pipeline.

O próximo marco é congelar um holdout sintético inédito que combine estados do
roteador, gateway, cliente e validador. Modelo local e corpus privado continuam
bloqueados, independentemente do resultado estrutural.
