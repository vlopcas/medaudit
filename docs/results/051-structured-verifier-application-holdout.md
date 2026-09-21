# Resultado 051: holdout da integração do verificador estruturado

## Objetivo

Avaliar uma única vez se a integração opt-in do `StructuredFactVerifier` com a
aplicação completa mantém compatibilidade, bloqueia contradições e não expõe
respostas retidas em casos sintéticos inéditos.

## Congelamento e execução

O dataset `structured_verifier_application_holdout.json`, política
`structured-verifier-application-holdout-v1`, foi congelado no commit `e6d7daa`
antes da primeira execução. Seu SHA-256 é
`80cf7f892d2487734baaf7a087c061568bf650d61b4342e33a79a6f24b0b71ac`.

O runner confere o hash e recusa sobrescrever o relatório:

```bash
docker compose run --rm evaluate-structured-verifier-application-holdout
```

O relatório local fica em
`artifacts/structured-verifier-application-holdout.local.json` e é ignorado
pelo Git.

## Resultado

- correspondência exata: 100% (9/9);
- segurança de liberação: 100% (9/9);
- uma paráfrase segura com ordem alterada foi liberada;
- contradições de unidade, quantidade, código e polaridade foram rejeitadas;
- claims parcial ou totalmente fora do domínio ficaram retidos para revisão;
- nenhuma resposta rejeitada ou retida foi exposta;
- abstention segura foi liberada;
- opt-in desligado preservou o comportamento anterior;
- nenhum modelo real, rede ou documento privado participou da execução.

## Decisão

A integração está aprovada como caminho experimental opt-in para o domínio
estreito do verificador. O holdout está encerrado e não será usado para ajuste.

Essa aprovação não promove a síntese local anteriormente reprovada, não amplia
o verificador para linguagem geral e não libera o runtime principal nem o
corpus privado. O próximo ciclo deve escolher entre exercitar a integração com
um modelo local em desenvolvimento sintético ou avançar para regras estruturadas,
sem reabrir este holdout.
