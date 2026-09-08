# ADR-007: Materialização temporal de chunks privados

## Status

Aceita em 2026-09-08.

## Contexto

O corpus contém versões com períodos de vigência diferentes. Indexar todas as
versões juntas permitiria recuperar uma regra correta para outra data, mas
incorreta para o caso analisado. O texto extraído também é privado e não pode
ser incorporado à imagem Docker, aos testes públicos ou ao Git.

## Decisão

Materializar chunks para uma data de referência explícita. O processamento
aceita somente entradas revisadas e vigentes, verifica a identidade por SHA-256
e resolve renomeações locais pelo mesmo hash. A saída é um JSONL privado em
`artifacts/chunks.local.jsonl`, gravado atomicamente.

Cada registro preserva versão e vigência do documento, página ou seção, IDs dos
elementos de origem e a estratégia de chunking. O terminal recebe somente
contagens agregadas. OCR permanece local e explícito; em PDFs híbridos, ele é
aplicado apenas às páginas sem texto nativo.


## Consequências

- uma execução representa um recorte temporal reproduzível;
- consultas históricas exigem nova materialização com a data correspondente;
- mudanças de caminho não quebram a associação se o conteúdo continuar igual;
- qualquer falha impede que o comando declare sucesso;
- o JSONL contém texto privado e nunca pode ser publicado;
- o volume de chunks deve ser medido antes de escolher embeddings ou banco
  vetorial.

O diagnóstico posterior agrega contagem e distribuição de caracteres por tipo
de mídia e estratégia, sem persistir texto ou identificadores no relatório.

## Como validar

- testar seleção por vigência e status de revisão;
- testar resolução de conteúdo renomeado por hash;
- rejeitar saídas sem o sufixo `.local.jsonl`;
- executar testes, lint e tipagem no Docker;
- validar o JSONL real apenas por contagens e estrutura.
