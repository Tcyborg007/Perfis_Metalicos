# Relatório de refatoração do Streamlit

## Escopo

As funções antigas listadas na auditoria de baseline foram rastreadas por nome em
todo o repositório. Foram removidas apenas as que não possuíam chamadas no fluxo
ativo:

- esforços e flecha por fórmulas fechadas duplicadas;
- cálculo antigo de `Cb`;
- rotinas antigas de FLT, FLM, FLA e cisalhamento;
- renderizadores antigos do memorial e do passo a passo.

Também foram removidas do `Config` as constantes normativas usadas exclusivamente
por essas rotinas. O Streamlit mantém somente código de apresentação, orquestração
e adaptadores; as resistências ativas permanecem em `calculos_nbr8800_2024.py` e
as novas primitivas auditáveis no pacote `src/perfis_metalicos`.

## Evidência

- 1.279 linhas removidas de `main.py`;
- nenhum dos símbolos removidos permanece definido ou referenciado;
- a suíte de caracterização e regressão permaneceu aprovada após a remoção;
- o comportamento de produção não foi substituído por novas fórmulas nesta etapa.

## Risco remanescente

`calculos_nbr8800_2024.py` ainda é um adaptador monolítico com resultados em
dicionários e contém partes normativas não integralmente migradas para resultados
tipados. Portanto, a ausência de equações no Streamlit não significa conclusão da
refatoração do núcleo nem validação normativa.
