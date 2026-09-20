# Resultado 042: modelo local pela aplicação de síntese

## Hipótese

O modelo local deveria atravessar a aplicação experimental completa com
respostas grounded válidas, conteúdo correto, comportamento repetível e
latência limitada, sem usar o corpus privado.

## Dataset e execução

O dataset público e integralmente sintético
`local_synthesis_application_development.json`, política
`local-synthesis-application-development-v1`, contém quatro casos: três
comparações respondíveis e uma consulta sem evidência suficiente. Seu SHA-256
na execução foi
`4dfa15c1dc4b6f44044789958b5d4e2d63dae9efafeb146efa66a605f662fcfb`.

Cada caso foi executado três vezes pela cadeia completa:

```text
roteamento → retrieval por passo → bundle → compilação selada
           → gateway → Qwen3-4B Q4_K_M → validação grounded
```

```bash
docker compose run --rm benchmark-local-synthesis-application
```

O cliente limitou a saída a 512 tokens. Cliente e servidor se comunicaram
somente pela rede interna do Docker. O relatório local contém apenas métricas,
contagens e IDs sintéticos; não conserva perguntas, evidências ou respostas do
modelo.

## Resultado

- preparação do request: 100% (12/12);
- exatamente uma invocação do cliente: 100% (12/12);
- liberação de saída grounded validada: 100% (12/12);
- acurácia do status: 25% (3/12);
- acurácia de conteúdo nos casos respondíveis: 0% (0/9);
- recall dos conceitos esperados: 0%;
- estabilidade exata, de status e de conteúdo: 100% (4/4 casos);
- latência média da aplicação: 436,58 ms;
- pior latência da aplicação: 712,49 ms;
- média de tokens de entrada: 279,75;
- média de tokens de saída: 22,25;
- a suíte passou com 252 testes;
- Ruff passou sem achados e mypy passou em 174 arquivos.

As três comparações respondíveis receberam
`insufficient_evidence` nas nove tentativas. O caso realmente insuficiente foi
classificado corretamente nas três tentativas. Portanto, a estabilidade
observada representa uma falha conservadora estável, não qualidade.

## Decisão

A cadeia de segurança e validação se comportou como projetado, mas a hipótese
de qualidade foi rejeitada. O modelo local não será promovido, a síntese segue
desabilitada por padrão e o corpus privado permanece bloqueado.

O próximo ciclo será um diagnóstico de desenvolvimento que compare o request
compilado vigente com a configuração local anteriormente bem-sucedida. Qualquer
nova candidata deverá ser formulada em desenvolvimento e avaliada em casos
sintéticos novos antes de consumir outro holdout.
