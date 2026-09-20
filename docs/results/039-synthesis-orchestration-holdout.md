# Resultado 039: holdout da orquestração de síntese

## Hipótese

A orquestração aprovada em desenvolvimento deveria preservar a correspondência
de estados e nunca liberar resposta sem validação, diante de combinações
inéditas do roteador, gateway, cliente falso e validador grounded.

## Protocolo

O holdout contém nove casos integralmente sintéticos sob a política
`synthesis-orchestration-holdout-v1`. Instrumento, configuração e dataset foram
congelados no commit `b57234b`, antes da execução, com SHA-256
`356fffc981c08f29136a688c041518ac55b7031fb073d7fe2c86fae1a7044bc6`.

Antes da abertura, a suíte reconstruída passou com 247 testes, Ruff sem achados
e mypy sem problemas em 169 arquivos. O dataset de desenvolvimento permaneceu
em 7/7. O holdout foi executado uma única vez, sem rede e com filesystem da
aplicação somente leitura. O relatório local está em
`artifacts/synthesis-orchestration-holdout.local.json`, com recusa de
sobrescrita.

```bash
docker compose run --rm evaluate-synthesis-orchestration-holdout
```

## Resultado

- correspondência exata: 100% (9/9);
- segurança de liberação: 100% (9/9);
- todas as nove categorias atingiram 100%;
- modo desabilitado, rota externa, clarificação, budget e revisão não chamaram
  o cliente nem liberaram resposta;
- uma afirmação com suporte válido nos dois grupos foi aceita;
- step desconhecido e citação duplicada foram rejeitados sem resposta;
- timeout sintético do cliente terminou sem resposta.

## Decisão

A orquestração está aprovada como fronteira estrutural experimental, opt-in e
com falha fechada. Isso autoriza somente uma composição de aplicação igualmente
opt-in que encadeie pipeline e orquestrador sem mudar os métodos existentes.

O holdout usou exclusivamente clientes falsos. Portanto, não promove o modelo
local, não autoriza corpus privado, não comprova qualidade factual e não ativa
síntese no runtime padrão. Qualquer avaliação de modelo continua sujeita aos
gates de qualidade já registrados.
