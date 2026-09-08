# ADR-006: Catálogo documental privado e revisado

## Status

Aceita em 2026-09-08.

## Contexto

Versão, vigência e relações de substituição são essenciais para auditoria, mas
não podem ser deduzidas com segurança somente a partir de nomes de arquivos.
Esses metadados também revelam informações sobre o corpus privado.

## Decisão

Manter um sidecar `catalog.local.json`, ignorado pelo Git. O bootstrap registra
identidade por SHA-256, caminhos locais, formato e tamanho. Campos semânticos
permanecem pendentes até revisão humana no documento de origem.

Entradas revisadas exigem título, família, organização, versão e início de
vigência. Relações `supersedes` devem apontar para IDs existentes, não podem
apontar para si mesmas nem formar ciclos. Atualizações preservam metadados
humanos pelo hash e mantêm documentos removidos com status `missing`.

Antes da ingestão, um gate determinístico exige status `reviewed`, confirma a
vigência na data de referência e compara o SHA-256 do conteúdo com o catálogo.
Qualquer falha interrompe o processamento com um motivo estável e sem registrar
nomes ou metadados privados.

## Consequências

- renomear um arquivo não perde os metadados revisados;
- cópias idênticas formam uma única identidade documental;
- alteração de conteúdo cria uma nova entrada pendente;
- o catálogo não pode ser publicado ou usado diretamente em testes públicos;
- conteúdo pendente, ausente, fora da vigência ou alterado é rejeitado antes do
  parsing e do chunking.

## Como validar

- testar duplicatas, períodos inválidos, referências desconhecidas e ciclos;
- provar round-trip determinístico da serialização;
- confirmar que o comando imprime apenas contagens;
- confirmar que o catálogo local permanece ignorado pelo Git.
