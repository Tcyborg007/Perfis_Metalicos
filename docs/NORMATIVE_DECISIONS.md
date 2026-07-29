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
| problema | definir, sem escolha silenciosa, quais coeficientes e categorias devem reger as combinações de uma edificação de aço quando a norma geral ABNT NBR 8681:2025 e a norma específica ABNT NBR 8800:2024 não apresentam catálogos idênticos |
| cópia NBR 8681 | segunda edição, 24.09.2025, SHA-256 `0D275BBE0B4408309D395F03A26836384E50A35CDB3AC406C8D1F2769FEC7FAE`; itens 5.1.3 a 5.1.6 e páginas numeradas 12 a 19 conferidos visualmente |
| cópia NBR 8800 | terceira edição, 02.10.2024, SHA-256 `13E77118CB83E6336D8CA197CB0DA68A5F4966983247ED205D6D2908C3A5080B`; itens 4.8.6 e 4.8.7 e páginas numeradas 19 a 24 conferidos visualmente |
| concordâncias verificadas | formas gerais das combinações ELU normal, especial/construção e excepcional; alternância da ação variável principal; uso de `ψ0`, `ψ1` e `ψ2`; combinações de serviço quase permanente, frequente e rara; coeficientes principais de ações permanentes diretas e de vento |
| divergência 1 — ações indiretas | a NBR 8681:2025, Tabela 3, separa protensão (`1,20/0,90`) de recalques e retração (`1,20/0`) e conserva `1,20/0,90` para protensão em combinação excepcional; a NBR 8800:2024, Tabela 1, apresenta uma única coluna de ações permanentes indiretas com `1,20/0` em combinações normais e especiais e `0/0` em excepcionais |
| divergência 2 — ocupação industrial | a nota c da Tabela 2 da NBR 8800 inclui edificações industriais na categoria `0,7/0,6/0,4`; a nota b da Tabela 6 da NBR 8681 cita comerciais, escritórios e acesso público, sem explicitar edificações industriais |
| divergência 3 — ações truncadas | a nota f da Tabela 2 da NBR 8800 define `ψ0 = ψ1 = ψ2 = 1,0`; a Tabela 6 da NBR 8681 não contém regra correspondente para ação truncada, exigindo que `γq` e `ψ` sejam modelados como classificações distintas |
| divergência 4 — pontes rolantes e pontes | a NBR 8800 inclui vigas de rolamento (`1,0/0,8/0,5`) e seus pilares/subestruturas (`0,7/0,6/0,4`); a NBR 8681 inclui vigas de rolamento, passarelas e pontes rodoviárias/ferroviárias, mas não explicita os pilares de suporte de vigas de rolamento |
| divergência 5 — situações excepcionais | a NBR 8800 admite `ψ2 = 0` para ação principal sísmica; a NBR 8681 permite reduzir `ψ2` por `0,7` quando a ação excepcional é fogo; são disposições específicas e não intercambiáveis |
| regra de prevalência a revisar | a NBR 8681:2025, 5.1.4 e 5.1.6, declara que seus valores podem ser alterados ou complementados por norma específica do tipo de estrutura/material; isso sustenta, mas não aprova automaticamente, o uso das disposições específicas da NBR 8800 para edificações de aço |
| alternativa A | usar o catálogo da NBR 8800:2024 em todo caso abrangido explicitamente por 4.8 e usar a NBR 8681:2025 apenas para requisitos não tratados, após verificar compatibilidade item a item |
| alternativa B | usar a NBR 8681:2025 como catálogo principal e substituir somente os casos explicitamente complementados pela NBR 8800:2024 |
| alternativa C | manter bases selecionáveis por contexto normativo, sem misturar coeficientes na mesma combinação; cada seleção exige justificativa e registro no memorial |
| decisão | nenhuma |
| implementação preventiva | o catálogo NBR 8681 é tipado em duas dimensões (`γq` e `ψ`), todas as regras possuem referência e permanecem `reviewed=False`; o gerador recusa utilizá-las |
| impacto atual | não há `CombinationRuleSet` normativo liberado para produção; a interface legada não pode ser promovida a fluxo validado |
| aprovação necessária | engenheiro estrutural habilitado deve selecionar e justificar uma alternativa, verificar a Errata 1:2025 da NBR 8800 e assinar ao menos um caso independente por família de combinação |
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
| decisão normativa detalhada | as alíneas 5.4.2.4-a/b/c da edição 2024 foram transcritas em caminho separado; a influência da Errata 1:2025 permanece pendente |
| implementação | `analysis.stability_segments`; uma única mesa continuamente contida exige classificação explícita da alínea, orientação/posição das forças e usa a demanda que comprime a mesa livre |
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
| parâmetro de seção | `Rm` é obrigatório; para seção duplamente simétrica o chamador deve declarar `Rm = 1,0` |
| limite aplicado | nenhum limite artificial é imposto ao resultado da expressão geral de 5.4.2.3-a |
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
