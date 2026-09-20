# Resultado 040: aplicação de síntese em desenvolvimento

## Hipótese

A composição de aplicação deve preservar rota, preparação e síntese numa única
operação, sem chamar o cliente antes de um request preparado e sem liberar
respostas não validadas.

## Dataset e execução

O dataset público e integralmente sintético
`synthesis_application_development.json`, política
`synthesis-application-development-v1`, contém seis fluxos. Seu SHA-256 na
execução foi
`df744bd215abd78d1a8fcdf9a8e4a9dcbeacaf32f4ec90bf3d4b860bc09ddb15`.

```bash
docker compose run --rm evaluate-synthesis-application
```

O serviço executou sem rede, com filesystem somente leitura e cliente falso.
Nenhum modelo ou corpus privado participou.

## Resultado

- correspondência exata: 100% (6/6);
- segurança de invocação: 100% (6/6);
- segurança de liberação: 100% (6/6);
- todas as seis categorias atingiram 100%;
- o padrão produziu request preparado, mas manteve síntese desabilitada e não
  chamou o cliente;
- rotas direta, externa e clarificação terminaram sem chamada ao cliente;
- resposta grounded válida foi liberada;
- resposta com citação fora do grupo foi rejeitada sem liberação;
- a suíte passou com 250 testes;
- Ruff passou sem achados e mypy passou em 172 arquivos.

## Decisão

A composição está aprovada somente no desenvolvimento sintético. Ela permanece
opt-in, não é um endpoint e não altera os métodos existentes.

O próximo marco é congelar um holdout sintético inédito da operação completa,
incluindo combinações temporais, revisão, budget e falhas do cliente. Modelo
local, qualidade factual e corpus privado continuam bloqueados.
