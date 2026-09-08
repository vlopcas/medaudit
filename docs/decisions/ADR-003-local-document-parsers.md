# ADR-003: Adaptadores locais para PDF, XLSX e XLS

## Status

Aceita em 2026-09-08.

## Contexto

O corpus privado possui PDFs e planilhas. A primeira ingestão precisa preservar
proveniência básica, operar sem serviços externos e consumir arquivos grandes
com uso de memória previsível.

## Opções consideradas

- ferramentas de parsing hospedadas em APIs;
- extração local com PyMuPDF e openpyxl;
- implementação própria dos formatos PDF e OOXML.

## Decisão

Usar PyMuPDF para extrair blocos textuais, página e bounding box de PDFs. Usar
openpyxl em modo somente leitura para representar cada linha não vazia de XLSX
como um elemento tabular atômico. Fórmulas XLSX são preservadas em vez de
substituídas por valores previamente calculados.

Usar xlrd exclusivamente para o formato histórico XLS. Nesse formato, o parser
recupera o último resultado calculado disponível; fórmulas originais, macros e
objetos incorporados não são preservados.

Os adaptadores recebem bytes e não acessam rede. OCR, imagens, detecção de
títulos, células mescladas e estrutura tabular avançada ficam explicitamente
fora desta primeira versão.

## Consequências

- documentos permanecem na máquina local;
- páginas e coordenadas de blocos PDF são rastreáveis;
- planilha e número da linha são rastreáveis;
- PDFs digitalizados podem resultar em zero elementos e exigirão OCR futuro;
- uma linha XLSX muito extensa permanece atômica;
- resultados de fórmulas XLS podem estar desatualizados em relação à fórmula.

## Como validar

- gerar PDF, XLSX e XLS sintéticos durante os testes;
- confirmar página, bounding box, planilha, linha e conteúdo esperado;
- rejeitar bytes inválidos com erros controlados;
- executar pytest, Ruff e mypy antes do checkpoint.
