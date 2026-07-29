# Questões normativas e de engenharia em aberto

Nenhuma questão desta lista pode ser resolvida por preferência de implementação. As respostas
devem citar cópia controlada, edição, item/página e decisão do engenheiro revisor.

## Documentos necessários

1. Fornecer a cópia legal da ABNT NBR 8800:2024/Er1:2025.
2. Fornecer a identificação exata e a cópia da NBR 6120:2019 versão corrigida e errata aplicável.
3. Fornecer a identificação exata e a cópia da NBR 6123:2023 versão corrigida e Errata 1:2025.
4. Identificar catálogos oficiais de Laminados, CS, CVS e VS, com edição e páginas.

## Decisões sobre ações e combinações

1. Aprovar uma das alternativas da decisão `ND-001` para compatibilizar a norma geral
   NBR 8681:2025 com a norma específica NBR 8800:2024.
2. Confirmar se a Errata 1:2025 da NBR 8800 altera algum coeficiente, nota ou equação de 4.8.
3. Definir o tratamento de protensão, ações truncadas, ocupação industrial, pilares que suportam
   vigas de rolamento, fogo e sismo nos limites do escopo da aplicação.
4. Quais categorias de ações e tabelas devem ser expostas pela aplicação sem permitir categoria
   livre não rastreada?
5. Quais ações favoráveis podem ser consideradas e em quais combinações?
6. Quais combinações especiais, de construção e excepcionais pertencem ao escopo inicial?

## Decisões sobre análise e estabilidade

1. Qual conjunto mínimo de vínculos permanece no escopo validado?
2. Como representar contenção lateral, torcional e de empenamento em cada extremidade de segmento?
3. Como classificar a eficácia de contenção contínua de apenas uma mesa?
4. Como tratar carga aplicada acima ou abaixo da semialtura e quais casos exigem análise racional?
5. Como tratar reversão de momento e mudança de mesa comprimida dentro do mesmo segmento?
6. Quais condições específicas de balanços devem ser implementadas antes de liberá-los?

## Decisões sobre resistência

1. Confirmar todas as equações e limites de FLT, FLM, FLA e Anexo E no baseline.
2. Confirmar quando `Wxc = Wx` é válido e quais propriedades provam dupla simetria.
3. Confirmar a formulação efetivamente alterada pela Errata 1:2025.
4. Definir a matriz de força localizada versus estado-limite aplicável.
5. Decidir se `local_flange_bending_strength()` deve ser integrada ou removida.
6. Definir a verificação completa de enrijecedores, soldas, contato e transferência.

## Decisões sobre ELS

1. Quais combinações e parcelas de deslocamento se aplicam a cada categoria?
2. Como representar sequência construtiva e instalação de elemento frágil?
3. Quando contraflecha pode ser deduzida e qual parcela limita essa dedução?
4. Qual limite corresponde a deslocamento absoluto e qual a deslocamento relativo?
5. Quais casos exigem verificação de vibração?

## Evidência e responsabilidade

1. Quem será o engenheiro responsável pela revisão normativa?
2. Quem realizará a revisão independente dos golden cases?
3. Quais softwares ou cálculos manuais independentes serão aceitos como referência?
4. Qual tolerância numérica será adotada por grandeza e algoritmo?
5. Qual política de assinatura, armazenamento e expiração será aplicada a evidências externas?
