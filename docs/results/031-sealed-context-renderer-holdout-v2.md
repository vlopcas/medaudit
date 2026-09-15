# Resultado 031: segundo holdout do renderer de contexto selado

## Hipótese e protocolo

Após corrigir e validar o harness, a fronteira selada deveria recusar mutações
inéditas e efetivas em associações, campos canônicos, memberships, inventário,
budget, identidade e ordem.

O dataset integralmente sintético foi congelado antes da execução no commit
`f979801`, com SHA-256
`3334cc0438c1a641d412fc6a4d93fc62a0da1bd49a6bd672a551b1c49eb8c7f4`.
O renderer não foi modificado depois do congelamento. O serviço validou o hash,
executou sem rede e materializou um relatório local protegido contra
sobrescrita:

```bash
docker compose run --rm evaluate-sealed-context-security-holdout-v2
```

## Resultado

- correspondência exata: 100% (11/11);
- controle íntegro aceito: 1/1;
- mutações inseguras recusadas: 100% (10/10);
- todas as dez categorias atingiram 100%;
- nenhuma transformação foi classificada como mutação nula pelo harness.

Os casos cobriram troca de páginas e seções, whitespace em escopo, normalização
Unicode de evidência, ordem de memberships compartilhados, remoção coordenada
de item e referência, mudança combinada de budget, membership indevido no
controle de consulta, reescrita coordenada de identidade e reordenação composta
de grupos.

## Decisão

A fronteira estrutural selada está aprovada para uma integração controlada e
explicitamente opt-in no pipeline. Isso significa que um caminho experimental
pode compilar, verificar e renderizar o contexto antes da síntese; não significa
ativá-lo por padrão nem aprovar a qualidade factual do modelo.

O SHA-256 sem chave continua sendo detecção de alteração interna, não
autenticação contra execução de código. Modelo local, corpus privado, decisões
clínicas e automação de auditoria não participaram deste gate e permanecem sem
promoção. O próximo marco é desenhar a integração opt-in com fallback fechado e
telemetria sem conteúdo sensível.
