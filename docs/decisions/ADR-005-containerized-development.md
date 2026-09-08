# ADR-005: Ambiente de desenvolvimento em Docker

## Status

Aceita em 2026-09-08.

## Contexto

O processamento documental depende de bibliotecas Python e de componentes do
sistema, como Tesseract e seus pacotes de idioma. Instalações manuais na máquina
reduzem reprodutibilidade e dificultam comparar resultados entre ambientes.

## Decisão

Docker Compose será o caminho recomendado para testes e ferramentas locais. A
imagem usa Python 3.12 e inclui Tesseract com português. Execuções não recebem
rede, removem capabilities Linux, impedem ganho de privilégios e usam filesystem
raiz somente leitura.

O corpus privado nunca entra no contexto efetivo da imagem. Para profiling,
`data/` é montado em runtime como somente leitura e os diagnósticos são gravados
separadamente em `artifacts/`, que é ignorado pelo Git.

O ambiente virtual nativo permanece disponível como alternativa rápida para
desenvolvimento, mas não é a referência de reprodutibilidade.

## Consequências

- dependências Python e OCR deixam de precisar de instalação global;
- construir a imagem requer rede, mas executar testes e profiling não;
- mudanças de dependência exigem reconstrução da imagem;
- arquivos gerados no bind mount usam o UID/GID configurado pelo host;
- acesso ao daemon Docker continua sendo uma responsabilidade do ambiente.

## Como validar

- inspecionar o contexto com `.dockerignore` antes do build;
- executar `docker compose run --rm checks`;
- confirmar português com `docker compose run --rm checks tesseract --list-langs`;
- executar o profiler e confirmar que o relatório está somente em `artifacts/`;
- confirmar que os serviços executam com rede e raiz do filesystem desativadas.

