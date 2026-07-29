# Hipóteses e limitações

## Classificação atual

**NÃO VALIDADO**

O aplicativo do commit-base não deve ser usado para emitir aprovação executiva, selecionar perfil
para fabricação ou substituir cálculo e revisão de engenheiro habilitado.

## Hipóteses do modelo existente

- viga prismática de um vão;
- vínculos ideais entre quatro modelos predefinidos;
- seção I/H duplamente simétrica;
- flexão no eixo forte;
- ações gravitacionais estáticas no plano da alma;
- carga distribuída uniforme em todo o vão;
- no máximo uma força pontual;
- comportamento elástico de primeira ordem para análise de esforços e deslocamentos;
- propriedades constantes E e I;
- unidades internas declaradas em kN e cm;
- propriedades do perfil tomadas diretamente de `perfis.xlsx`;
- coeficientes e categorias escolhidos manualmente na interface.

## Limitações computacionais conhecidas

- não suporta coleção genérica de ações;
- não alterna todas as ações variáveis como principais;
- não gera envelope de combinações;
- não representa carregamento parcial, trapezoidal, triangular, vários pontos ou momentos aplicados;
- não resolve a posição da flecha máxima por rotação nula;
- não modela segmentos de contenção nem mesa comprimida por segmento;
- não separa contenção lateral, torcional e de empenamento;
- não verifica todos os requisitos de enrijecedores, soldas e transferência;
- não possui matriz completa de forças localizadas;
- não decompõe deslocamentos por fase e parcela;
- não implementa vibração;
- não valida a origem do catálogo;
- não exige evidência documental externa no modo manual;
- não possui estados tipados capazes de bloquear aprovação com pendência.

## Fora do escopo declarado até implementação validada

- barras com força axial;
- torção e flexão biaxial;
- estabilidade global de edifícios;
- ligações;
- vigas e pilares mistos;
- perfis formados a frio;
- incêndio e sismo;
- aberturas na alma;
- fadiga;
- vibração;
- empoçamento;
- pares de forças localizadas opostas;
- painel de alma de ligação;
- vento calculado a partir da geometria da edificação;
- balanços ou sistemas diferentes dos quatro modelos atuais, salvo novo modelo validado.

## Limitações normativas

- apenas a cópia original da NBR 8800:2024 está disponível;
- a Errata 1:2025 da NBR 8800 não foi fornecida;
- NBR 8681:2025, NBR 6120:2019 corrigida e NBR 6123:2023 corrigida/Er1:2025 não foram fornecidas;
- referências existentes no baseline ainda não foram revisadas item a item;
- não existe engenheiro responsável designado para a revisão normativa;
- não existem resultados independentes assinados;
- não existe certificação do software.

## Regra de segurança

Qualquer entrada que acione uma limitação obrigatória deve produzir estado bloqueante
(`NOT_CHECKED`, `OUT_OF_SCOPE`, `INVALID_INPUT` ou `EXTERNAL_EVIDENCE_REQUIRED`), nunca aprovação.
Essa regra ainda não está implementada no commit-base.
