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
- a interface ainda não usa o solver novo que representa carregamento parcial, linear variável,
  vários pontos e momentos aplicados;
- a interface ainda usa o motor legado para flecha; o solver novo resolve rotação nula por
  elemento e registra erro de refinamento;
- o núcleo novo modela segmentos, mesa comprimida e contenções lateral/torcional/empenamento,
  porém ainda não está integrado à interface de produção;
- a eficácia, resistência, rigidez e ligação das contenções não são dimensionadas pelo núcleo;
- o caso de uma única mesa continuamente contida permanece bloqueado até a revisão completa de
  5.4.2.4;
- balanços permanecem bloqueados na seleção de `Cb` até a classificação explícita das restrições;
- não verifica todos os requisitos de enrijecedores, soldas e transferência;
- não possui matriz completa de forças localizadas;
- não decompõe deslocamentos por fase e parcela;
- não implementa vibração;
- não valida a origem do catálogo;
- a interface exige arquivo e metadados de evidência externa, mas ainda não importa resultados
  numéricos assinados para comparação;
- os estados tipados e o agregador seguro existem; partes legadas ainda precisam ser removidas
  para que todo o fluxo use exclusivamente esse domínio.

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
Essa regra está implementada no novo domínio e na ponte de segurança do modo manual, mas a
migração integral do fluxo legado ainda é uma pendência obrigatória.
