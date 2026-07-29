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

- o núcleo suporta coleção genérica de ações, alterna variáveis principais e gera envelope, mas
  não possui regras normativas de produção enquanto a NBR 8681:2025 não for fornecida e revisada;
- a interface ainda não usa o solver novo que representa carregamento parcial, linear variável,
  vários pontos e momentos aplicados;
- a interface ainda usa o motor legado para flecha; o solver novo resolve rotação nula por
  elemento e registra erro de refinamento;
- o núcleo novo modela segmentos, mesa comprimida e contenções lateral/torcional/empenamento,
  porém ainda não está integrado à interface de produção;
- a eficácia, resistência, rigidez e ligação das contenções não são dimensionadas pelo núcleo;
- o caso de uma única mesa continuamente contida possui caminhos separados para 5.4.2.4-a/b/c
  da edição 2024; influência eventual da Errata 1:2025 e dimensionamento da contenção permanecem
  pendentes;
- balanços permanecem bloqueados na seleção de `Cb` até a classificação explícita das restrições;
- não verifica todos os requisitos de enrijecedores, soldas e transferência; a triagem geométrica
  é separada e não aumenta `kv` nem libera aprovação;
- possui matriz tipada de aplicabilidade para forças localizadas, mas a UI automática ainda
  representa apenas compressão e não coleta todas as classificações de 5.7.1; transferência por
  solda, condições de 5.7.8 e dimensionamento de 5.7.9 permanecem bloqueantes;
- o domínio novo decompõe deslocamentos por fase e parcela, mas o fluxo de produção ainda usa
  flecha total simplificada e por isso permanece `NOT_CHECKED`;
- não implementa vibração;
- valida hash e coerências automáticas do catálogo, mas a origem oficial das quatro famílias não
  foi fornecida; cinco designações estão duplicadas na família VS e o status atual é
  `INVALID_CATALOG_DATA`;
- a interface exige arquivo e metadados de evidência externa, mas ainda não importa resultados
  numéricos assinados para comparação;
- as equações antigas e sem chamadas foram removidas do Streamlit; o adaptador monolítico
  `calculos_nbr8800_2024.py` ainda precisa ser integralmente migrado para resultados tipados.

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

O texto do adaptador legado não declara mais que a Errata 1:2025 foi verificada. Toda referência
à expressão de `j` atribuída à errata é emitida com `NORMATIVE_REVIEW_REQUIRED`.

## Regra de segurança

Qualquer entrada que acione uma limitação obrigatória deve produzir estado bloqueante
(`NOT_CHECKED`, `OUT_OF_SCOPE`, `INVALID_INPUT` ou `EXTERNAL_EVIDENCE_REQUIRED`), nunca aprovação.
Essa regra está implementada no novo domínio e na ponte de segurança do modo manual, mas a
migração integral do fluxo legado ainda é uma pendência obrigatória.
