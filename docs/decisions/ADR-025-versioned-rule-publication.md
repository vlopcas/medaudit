# ADR-025: publicação de regras é versionada e falha fechada

## Status

Aceita para desenvolvimento sintético.

## Contexto

Passar pela auditoria e pelo gate de admissão não basta para tornar um catálogo
publicável. A fronteira precisa impedir mutação de versões já identificadas,
substituição silenciosa e perda de provenance entre snapshots.

## Decisão

- a publicação recalcula a admissão; resultados bloqueados ou em revisão nunca
  produzem catálogo;
- cada snapshot publicado recebe identidade SHA-256 determinística sobre as
  regras estruturadas ordenadas;
- o snapshot conserva integralmente `rule_id`, versão e documento de origem;
- alterar o conteúdo de uma identidade `rule_id@version` já publicada é
  proibido;
- versões novas do mesmo `rule_id` devem ser monotônicas e referenciar
  explicitamente o par anterior/novo revisado;
- referências de substituição que não correspondem à mudança atual são
  recusadas;
- remoções silenciosas ficam em revisão;
- LLMs não participam da admissão, comparação ou publicação.

## Consequências

O snapshot é reproduzível e mudanças de versão são explícitas, mas o primeiro
contrato ainda não permite aprovar uma aposentadoria legítima. Essa capacidade
deve ser modelada em novos casos de desenvolvimento antes de qualquer holdout.
Persistência, assinatura, controle de acesso e catálogo privado permanecem fora
do escopo.
