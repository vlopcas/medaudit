# ADR-013: baseline determinístico de Query Understanding

## Status

Aceita em 2026-09-12.

## Contexto

O pipeline recebia toda consulta diretamente no retriever. A Fase 8 exige uma
fronteira anterior capaz de explicitar intenção, data, entidades e necessidades
de decomposição ou dados externos. Usar imediatamente um LLM dificultaria saber
se a complexidade acrescentada melhora o roteamento.

## Decisão

O primeiro contrato é `QueryAnalysis`, produzido por um
`DeterministicQueryAnalyzer` sem rede, modelo ou acesso ao corpus. Ele preserva
a pergunta original, normaliza apenas espaços, usa uma taxonomia pequena de
intenções e extrai somente sinais conservadores: data explícita nos formatos
ISO ou brasileiro e código de procedimento com oito dígitos.

Regras lexicais interpretáveis sinalizam dados externos e decomposição. Duas
datas exigem decomposição e impedem a escolha silenciosa de uma única data.
Datas inválidas falham explicitamente. O campo de plano permanece vazio até
existir uma regra ou avaliação que justifique sua extração.

Este marco ainda não altera a consulta enviada ao retriever, não cria
subconsultas e não habilita ferramentas externas.

## Consequências

- o baseline pode ser testado e inspecionado sem um segundo modelo;
- falsos positivos e falsos negativos permanecem atribuíveis a regras claras;
- a taxonomia inicial é limitada e deverá ser medida em dados sintéticos antes
  de orientar o pipeline;
- extração de entidades clínicas livres e reescrita continuam fora do escopo.

## Como validar

- usar somente perguntas e identificadores sintéticos;
- cobrir cada intenção e os sinais de roteamento;
- testar datas ISO, brasileiras, múltiplas e inválidas;
- provar que espaços são normalizados sem reescrever o significado;
- manter o analisador independente de retrieval, LLM e corpus privado.
