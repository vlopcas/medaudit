# Resultado 052: verificação estruturada com modelo local

## Hipótese

A integração opt-in do `StructuredFactVerifier` poderia aumentar a segurança da
aplicação com o Qwen3-4B local sem reduzir excessivamente a utilidade das
respostas sintéticas suportadas.

## Estratégia e dataset

O dataset integralmente sintético
`local_structured_verifier_application_development.json`, política
`local-structured-verifier-application-development-v1`, tem SHA-256
`8a21c654fd7993f3ceb6b8cbee9225963933ebee036badf719e48e29f69ea291`.
Ele contém comparações de quantidade, código e polaridade, além de um caso sem
evidência suficiente. Cada caso foi executado três vezes pela aplicação completa
com instrução explícita, schema limitado e o modelo local.

Dois braços usaram exatamente o mesmo dataset e configuração:

```bash
docker compose run --rm benchmark-local-structured-verifier-application-baseline
docker compose run --rm benchmark-local-structured-verifier-application
```

Os relatórios locais são ignorados pelo Git e não armazenam o texto gerado.

## Resultado

### Controle sem verificador

- 12/12 saídas validadas;
- acurácia de status: 100%;
- acurácia de conteúdo respondível: 100%;
- recall dos conceitos esperados: 100%;
- segurança de liberação: 100%;
- nenhuma liberação insegura;
- estabilidade exata, de status e de conteúdo: 100%.

### Com verificador estruturado

- seis saídas validadas e seis retidas;
- acurácia de status: 50%;
- acurácia de conteúdo respondível: 33,3%;
- recall dos conceitos esperados: 50%;
- segurança de liberação: 100%;
- nenhuma liberação insegura;
- quantidade e código foram retidos nas três repetições;
- polaridade e abstention foram liberadas nas três repetições;
- estabilidade exata, de status e de conteúdo: 100%.

A suíte encerrou com 265 testes, Ruff e mypy limpos em 183 arquivos.

## Decisão

A composição com o modelo local foi rejeitada no desenvolvimento e não seguirá
para holdout. O controle já tinha 100% de segurança e conteúdo; o verificador
não bloqueou uma liberação insegura adicional e reduziu a utilidade respondível
de 100% para 33,3%.

Isso não invalida o contrato de verificação nem os resultados determinísticos
anteriores. Mostra que exigir um fato reconhecido em todo claim não é compatível
com a forma estrutural usada pelo modelo, mesmo quando o conteúdo agregado está
correto. O componente permanece experimental para respostas canônicas e não é
promovido ao caminho do modelo local. Corpus privado e runtime continuam
bloqueados.
