# ADR-019: compilação de contexto é uma fronteira explícita

## Contexto

O contrato de síntese decomposta montava diretamente o payload do modelo a
partir dos grupos de evidência. Isso preservava citações, mas não representava
orçamento, confiança, exclusões ou motivos de recusa como conceitos de domínio.
O holdout do detector por expressões regulares também mostrou que classificar
texto isoladamente não estabelece uma fronteira de segurança generalizável.

## Opções consideradas

1. Continuar concatenando prompt e evidências em cada construtor de request.
2. Acoplar automaticamente o detector por regex ao caminho generativo.
3. Introduzir um compilador provider-neutral anterior à renderização do modelo.

## Decisão

Adotar a terceira opção como componente inicialmente isolado. O compilador:

- mantém instrução, consulta e evidência em itens estruturalmente distintos;
- marca somente instruções como controle confiável;
- conserva IDs, passos e coordenadas de provenance das evidências;
- usa uma interface de estimativa de tokens substituível;
- aplica orçamento antes da renderização para qualquer provider;
- deduplica identidades iguais e exige revisão para identidades conflitantes;
- aceita IDs de revisão por uma fronteira explícita, sem promover o detector
  experimental reprovado;
- produz estados `ready`, `insufficient_evidence`, `budget_exceeded` ou
  `needs_review` antes de qualquer chamada de modelo.

Um renderer opt-in pode converter somente contextos `ready` no `LLMRequest`
decomposto. Ele revalida budget, inventário, confiança, IDs e vínculos por passo
antes de produzir o payload. O runtime continua sem adotar esse caminho por
padrão.

## Consequências

Há um lugar único para explicar por que cada item foi incluído ou excluído e
quanto orçamento consumiu. A separação estrutural reduz concatenações livres,
mas não torna o conteúdo documental confiável e não substitui isolamento do
provider, validação da resposta ou revisão humana.

A estimativa padrão por bytes é determinística, não exata. Um adaptador futuro
poderá usar o tokenizer do modelo sem alterar o contrato. A política de seleção
inicial também é deliberadamente simples e deverá ser comparada antes de ganhar
compressão, reranking ou outras heurísticas.

O renderer foi comparado ao construtor de request anterior e produziu o mesmo
contrato, payload e schema para um pacote sem exclusões. Contextos bloqueados ou
adulterados falham antes de qualquer chamada de modelo.

## Como validar

- testar separação de tipos e níveis de confiança;
- testar orçamento insuficiente sem liberar geração parcial;
- testar deduplicação e conflito de identidade;
- testar revisão sem reter texto rejeitado no resultado;
- avaliar o contrato em desenvolvimento e depois em holdout sintético inédito;
- manter o componente fora do runtime até esses gates serem aprovados.
