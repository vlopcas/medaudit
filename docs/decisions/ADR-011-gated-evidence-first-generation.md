# ADR-011: geração condicionada a evidências rastreáveis

## Status

Aceita em 2026-09-12.

## Contexto

O retriever BM25 e a política de abstention já foram medidos e congelados. A
próxima fronteira precisa preparar respostas fundamentadas sem permitir que um
modelo generativo responda quando o retrieval considerar a evidência
insuficiente. Também é necessário impedir que a saída cite chunks que não
foram entregues ao modelo.

## Decisão

O pipeline executa retrieval e calcula os sinais de confiança antes de qualquer
chamada generativa. A política carregada em runtime precisa ter status
`frozen`, usar o score máximo e o operador inclusivo definidos na calibração.
Políticas candidatas são recusadas.

Quando o limiar não é atingido, o resultado é `insufficient_evidence`, não
contém passagens e não pode originar uma requisição ao LLM. Quando aceito, cada
evidência carrega texto somente em memória e uma localização com IDs do chunk e
documento, posição no ranking, score, página e seção.

A requisição ao modelo é independente de fornecedor, tem temperatura zero,
trata as passagens como dados não confiáveis e exige saída estruturada. A
resposta passa por uma segunda validação determinística: respostas afirmativas
precisam de texto e ao menos uma citação; toda citação deve pertencer ao pacote
recuperado; abstention do próprio modelo precisa ter resposta e citações
vazias.

Este marco prepara a integração, mas não escolhe nem executa um modelo local.
Também não afirma que uma citação válida implica que a passagem realmente
suporta cada afirmação; essa medição pertence ao futuro verifier.

## Consequências

- o modelo não pode contornar a política de abstention;
- citações inventadas ou fora do contexto são rejeitadas;
- o texto privado não precisa ser persistido em novos artefatos;
- o contrato permite trocar o provedor ou modelo sem alterar o domínio;
- correção factual e suporte por claim ainda exigem avaliação própria.

## Como validar

- usar somente chunks sintéticos nos testes versionados;
- rejeitar política candidata ou formato desconhecido;
- provar que abstention impede a construção do prompt;
- aceitar somente IDs presentes nas evidências selecionadas;
- rejeitar respostas afirmativas sem texto ou citação.
