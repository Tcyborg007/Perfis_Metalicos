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
| status | `PARTIAL_IMPLEMENTATION` |
| problema | a UI permite tornar FLT globalmente não aplicável por uma seleção única |
| fundamento de segurança | a aplicabilidade depende de segmento, sinal do momento, mesa comprimida e tipo de contenção |
| decisão de software | o checkbox global foi removido; a arquitetura nova classifica contenções por mesa, extremidade e intervalo e não desativa FLT globalmente |
| decisão normativa detalhada | pendente de revisão da NBR 8800:2024/Er1:2025 por item |
| implementação | `analysis.stability_segments`; uma única mesa continuamente contida segue caminho separado e bloqueante |
| testes | `tests/test_flt_segments.py` |
| revisor estrutural | não designado |
| data | não definida |

## ND-004 - Associação de Cb, demanda e resistência ao trecho

| Campo | Registro |
|---|---|
| status | `PARTIAL_IMPLEMENTATION` |
| problema | o baseline calculava um único `Cb` e podia associá-lo à demanda global, sem provar identidade de trecho |
| evidência consultada | cópia fornecida da ABNT NBR 8800:2024, item 5.4.2.3, páginas numeradas 54 e 55 (páginas físicas 71 e 72 do PDF), inspecionadas visualmente |
| decisão de software | `Mmax`, `MA`, `MB`, `MC`, `Cb`, demanda, resistência e utilização são objetos do mesmo `UnbracedSegment`; o governante é escolhido pela utilização |
| limite aplicado | `Cb <= 3,0` no caso geral do item 5.4.2.3-a |
| barreiras | carga acima da semialtura, balanço não classificado, contenção insuficiente e uma única mesa continuamente contida não recebem resultado numérico liberado |
| teste de regressão obrigatório | `test_each_segment_uses_its_own_moments_cb_demand_and_resistance` |
| pendência | equações de resistência de FLT e eficácia/dimensionamento das contenções ainda exigem revisão completa e evidência independente |
| revisor estrutural | não designado |
| data | não definida |

## ND-005 - Fronteiras das funções por partes do Anexo D

| Campo | Registro |
|---|---|
| status | `PARTIAL_IMPLEMENTATION` |
| evidência consultada | ABNT NBR 8800:2024, D.2.1 e D.2.2, páginas numeradas 137 e 138 |
| decisão de software | `λ <= λp` seleciona o ramo plástico/escoamento; `λp < λ <= λr` seleciona o ramo inelástico; `λ > λr` seleciona o ramo elástico |
| procedimento alternativo de FLT | limites de `λLT` em 0,4 e 1,4 centralizados em `ltb_alternative_reduction` |
| observação numérica | as expressões publicadas dos ramos inelástico e elástico do procedimento alternativo apresentam diferença relativa inferior a 0,05 % imediatamente acima de 1,4; o teste registra essa transição sem “corrigir” coeficiente normativo |
| testes | `tests/test_flexure_piecewise.py` |
| pendência | parâmetros específicos de cada estado-limite e a Errata 1:2025 ainda exigem revisão e evidência independente |
| revisor estrutural | não designado |
| data | não definida |
