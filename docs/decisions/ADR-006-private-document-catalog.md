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

## Consequências

- renomear um arquivo não perde os metadados revisados;
- cópias idênticas formam uma única identidade documental;
- alteração de conteúdo cria uma nova entrada pendente;
- o catálogo não pode ser publicado ou usado diretamente em testes públicos;
- ingestão temporal deverá aceitar somente entradas revisadas.

## Como validar

- testar duplicatas, períodos inválidos, referências desconhecidas e ciclos;
- provar round-trip determinístico da serialização;
- confirmar que o comando imprime apenas contagens;
- confirmar que o catálogo local permanece ignorado pelo Git.
