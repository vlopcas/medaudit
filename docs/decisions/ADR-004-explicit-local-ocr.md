# ADR-004: OCR local como fallback explícito

## Status

Aceita em 2026-09-08.

## Contexto

Parte dos PDFs pode não possuir camada textual. Aplicar OCR a todos os arquivos
aumentaria muito a latência e poderia substituir texto nativo de melhor
qualidade por uma interpretação com erros.

## Decisão

Manter a extração textual como caminho primário. Um parser separado identifica
páginas sem texto e aplica OCR somente nelas, quando escolhido explicitamente.
O primeiro provedor usa Tesseract local por meio do PyMuPDF e registra seu nome
na proveniência de cada elemento.

Se OCR for necessário e o executável local não estiver disponível, o pipeline
falha claramente. Não haverá fallback para serviço externo.

## Consequências

- documentos textuais não pagam o custo de OCR;
- páginas nativas e páginas OCR podem coexistir com proveniência distinta;
- idioma e DPI fazem parte da configuração do provedor;
- resultados OCR precisarão de avaliação específica;
- o executável e os pacotes de idioma Tesseract são dependências do ambiente,
  não dependências Python instaladas silenciosamente.

## Como validar

- usar PDFs sintéticos com páginas textuais e vazias;
- provar que somente páginas vazias acionam OCR;
- provar que indisponibilidade local gera erro explícito;
- manter testes independentes de Tesseract usando um provedor falso.
