# ADR-008: Avaliação privada de retrieval antes de embeddings

## Status

Aceita em 2026-09-08.

## Contexto

O corpus processado está pronto para busca, mas adotar embeddings sem um golden
set impediria saber se a complexidade trouxe ganho. Perguntas, julgamentos de
relevância e resultados por caso também podem revelar informações privadas.

## Decisão

Avaliar primeiro BM25 sobre os chunks privados. O golden set local declara uma
data de referência e permite relevância no nível de documento ou de chunk, mas
nunca ambos no mesmo caso. Casos sem referências medem abstention.

O avaliador exige que a data do golden set corresponda à materialização,
rejeita referências desconhecidas e grava detalhes somente em um arquivo
`.local.json`. O terminal mostra métricas agregadas e nunca perguntas, conteúdo
identificadores recuperados ou nomes de categorias.

## Consequências

- a primeira rotulagem pode ser feita no nível de documento;
- relevância de chunks pode ser adicionada gradualmente;
- Hit Rate, Recall, MRR e abstention formam a baseline comparável;
- `top_k` e limiar mínimo de score precisam ser registrados por experimento;
- embeddings só serão justificáveis se superarem essa baseline no mesmo set.

Candidatos gerados externamente passam por uma fila privada. O sistema pode
mapear rótulos de fonte para IDs do catálogo, mas mantém todos os casos como
`pending` até uma pessoa revisar pergunta, resposta, citação, data e relevância.
Depois da aprovação, o finalizador agrupa casos por data de referência e aplica
uma data explícita aos casos originalmente sem data. A baseline inicial usa
relevância documental; a rotulagem por chunk é uma etapa posterior.

Uma auditoria temporal obrigatória verifica se cada documento relevante estava
vigente na data do caso. Conflitos são registrados apenas em relatório privado
e impedem a execução da baseline até revisão humana.

A baseline temporal materializa e avalia cada data isoladamente. As métricas
globais são médias ponderadas pelas quantidades de casos aplicáveis, evitando
que snapshots pequenos tenham o mesmo peso de snapshots maiores.

O diagnóstico cruza resultados e metadados revisados somente em relatório
privado. O terminal limita-se às quantidades de zero hit, recall parcial e
abstention incorreta.

Antes de definir uma política de abstention, medir isoladamente score máximo,
margem normalizada, cobertura da consulta, cobertura de termos raros e
concentração por documento. Pesos e limiares não serão escolhidos no conjunto
completo usado para reportar a baseline.

Após ampliar o benchmark, uma divisão determinística e estratificada por
respondibilidade separa calibração e avaliação final. Todos os experimentos e
ajustes usam somente calibração. A partição final permanece sem consulta até a
política e seus limiares serem congelados. O manifesto local registra seed,
fingerprint e IDs para detectar alterações, omissões e sobreposição.

## Como validar

- testar relevância por documento e por chunk;
- rejeitar níveis misturados, IDs desconhecidos e datas incompatíveis;
- provar que relatório e terminal não contêm perguntas;
- manter golden set e relatório reais ignorados pelo Git.
