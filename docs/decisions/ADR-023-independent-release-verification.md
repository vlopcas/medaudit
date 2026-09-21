# ADR-023: verificação independente antes da liberação

## Contexto

O holdout da síntese local mostrou que respostas podem cumprir o schema e citar
somente evidências autorizadas, mas ainda assim errar abstention ou falhar um
contrato de conteúdo adversarial. Validação estrutural não equivale a suporte
semântico nem a segurança da resposta.

## Decisão

Introduzir uma fronteira opcional de verificação depois da validação grounded e
antes da liberação:

- o verificador recebe somente a resposta já estruturada e o bundle autorizado;
- geração e verificação usam contratos separados;
- as decisões possíveis são liberar, rejeitar ou encaminhar para revisão;
- códigos de motivo pertencem a um enum fechado e não carregam conteúdo;
- rejeição e revisão nunca retornam a resposta ao consumidor;
- exceção ou resultado inválido do verificador falha fechado;
- resposta estruturalmente inválida é recusada antes de chamar o verificador;
- ausência de verificador preserva o comportamento existente;
- o caminho padrão continua com síntese desabilitada.

## Consequências

A fronteira permite comparar estratégias determinísticas, modelos independentes
ou revisão humana sem acoplá-las ao gerador. Ela não fornece por si só um
algoritmo de entailment, não transforma citações em prova semântica e não
promove o modelo local.

O primeiro ciclo usa somente clientes e verificadores falsos. Uma estratégia
real deve ser formulada e avaliada em novos casos de desenvolvimento antes de
qualquer holdout.
