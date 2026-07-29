# Registro de decisões normativas

## Regra

Uma decisão somente passa a `APPROVED` quando contém:

- documentos controlados consultados;
- item e página;
- alternativas analisadas;
- impacto no código e nos resultados;
- decisão;
- nome, registro profissional e data do engenheiro revisor;
- teste independente associado.

## ND-001 - NBR 8800:2024 versus NBR 8681:2025

| Campo | Registro |
|---|---|
| status | `NORMATIVE_REVIEW_REQUIRED` |
| problema | o baseline implementa combinações simplificadas com referências internas da NBR 8800:2024, enquanto o escopo exige compatibilidade explícita com a NBR 8681:2025 |
| evidência disponível | NBR 8800:2024 original; a própria norma remete à NBR 8681 e contém ao menos uma nota que identifica a edição 2003 |
| evidência ausente | texto integral e metadado controlado da NBR 8681:2025; Errata 1:2025 da NBR 8800 |
| alternativas | ainda não formuladas, para evitar inferência sem fonte |
| decisão | nenhuma |
| impacto atual | o mecanismo genérico aceita múltiplas ações e fatores rastreados, mas não há `CombinationRuleSet` de produção; somente fatores `TEST_ONLY` são exercitados |
| revisor estrutural | não designado |
| data | não definida |

## ND-002 - Expressão atribuída à Errata 1:2025

| Campo | Registro |
|---|---|
| status | `NORMATIVE_REVIEW_REQUIRED` |
| problema | `shear_strength_i()` declara que a expressão de `j` foi corrigida pela Errata 1:2025 |
| evidência disponível | comentário e teste internos; cópia original da NBR 8800:2024 |
| evidência ausente | cópia integral da Errata 1:2025 |
| decisão | preservar o baseline sem promover a alegação a “verificada” |
| impacto atual | função não pode ser classificada como normativamente validada |
| revisor estrutural | não designado |
| data | não definida |

## ND-003 - Contenção contínua e aplicabilidade global da FLT

| Campo | Registro |
|---|---|
| status | `REJECTED_BASELINE_BEHAVIOR_PENDING_IMPLEMENTATION` |
| problema | a UI permite tornar FLT globalmente não aplicável por uma seleção única |
| fundamento de segurança | a aplicabilidade depende de segmento, sinal do momento, mesa comprimida e tipo de contenção |
| decisão de software | o comportamento global não será mantido na arquitetura nova |
| decisão normativa detalhada | pendente de revisão da NBR 8800:2024/Er1:2025 por item |
| revisor estrutural | não designado |
| data | não definida |
