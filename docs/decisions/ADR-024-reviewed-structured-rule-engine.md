# ADR-024: regras estruturadas revisadas são executadas deterministicamente

## Status

Aceita para desenvolvimento sintético.

## Contexto

Vigência documental e snapshots temporais já existem, mas texto recuperado não
deve decidir silenciosamente permissão, cobertura ou pagamento. Regras
formalizáveis precisam de tipos, versões, condições, prioridade, vigência e
provenance explícitos.

## Decisão

- o motor recebe somente regras previamente estruturadas e revisadas;
- cada regra possui identidade e versão, escopo, decisão fechada, período de
  vigência inclusivo, prioridade, condições exatas e documento de origem;
- consultas informam escopo, data de referência e atributos explicitamente;
- a maior prioridade aplicável vence;
- decisões divergentes na mesma maior prioridade resultam em revisão;
- ausência de regra aplicável é um estado explícito, nunca uma permissão
  implícita;
- toda decisão aplicada conserva IDs e versões das regras que a sustentam;
- antes da admissão, pares de regras de mesma prioridade e escopo são auditados
  estaticamente quanto a vigências e condições compatíveis;
- sobreposições divergentes são conflitos; sobreposições equivalentes exigem
  revisão de redundância;
- LLMs não participam da execução e não resolvem conflitos.

## Consequências

O baseline é pequeno e explicável, mas ainda não oferece linguagem de condições
complexas, composição booleana, importação do catálogo privado ou workflow de
aprovação. Extração de regras a partir de documentos será uma fronteira separada
e não poderá publicar regras sem revisão. O gate bloqueante já existe para o
contrato sintético, mas ainda não foi conectado a catálogo privado nem a um
workflow real de publicação.
