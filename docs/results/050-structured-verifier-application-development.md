# Resultado 050: integração do verificador estruturado à aplicação

## Hipótese

O `StructuredFactVerifier` poderia ser injetado de forma opt-in na aplicação de
síntese existente, sem mudar o comportamento padrão e sem permitir que respostas
rejeitadas ou retidas atravessassem a fronteira de liberação.

## Estratégia e dataset

A avaliação percorre a composição real `GroundedSynthesisApplication`, incluindo
roteamento, retrieval, execução por passo, compilação de contexto, cliente falso,
validação estrutural e verificação. Nenhum atalho chama o verificador diretamente.

O dataset público e sintético
`structured_verifier_application_development.json`, política
`structured-verifier-application-development-v1`, possui SHA-256
`e7e56bf3c3470d8de102bd50beea4adf7cee61b9ac554dc47e067adae51dc461` e
sete fluxos:

- compatibilidade com o opt-in desligado;
- liberação de fatos suportados;
- rejeição de contradições de quantidade, código e polaridade;
- retenção de linguagem fora do domínio estruturado;
- liberação de abstention segura.

```bash
docker compose run --rm evaluate-structured-verifier-application
```

## Resultado

- correspondência exata: 100% (7/7);
- segurança de liberação: 100% (7/7);
- nenhuma resposta rejeitada ou retida foi exposta;
- o verificador não foi chamado quando o opt-in estava desligado;
- com o opt-in ligado, o verificador foi chamado exatamente uma vez por saída
  estruturalmente válida;
- 264 testes, Ruff e mypy passaram em 183 arquivos.

## Decisão

A integração está aprovada em desenvolvimento como caminho experimental opt-in.
O comportamento padrão permanece inalterado e a aprovação continua limitada a
quantidades com unidade, códigos e polaridade. Linguagem não reconhecida exige
revisão.

O próximo gate, se necessário, é um holdout sintético inédito da integração,
congelado antes da primeira execução. Modelo local, runtime principal e corpus
privado permanecem bloqueados.
