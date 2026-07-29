# Changelog

## [Unreleased]

### Added

- domínio tipado de unidades, ações, resultados e evidências;
- gerador genérico de combinações dirigido por regras rastreadas;
- solver de viga prismática com múltiplas cargas e erro controlado;
- FLT associada ao próprio trecho destravado, com mesa comprimida e contenções;
- funções por partes centralizadas e testes de fronteira;
- matriz de forças localizadas e ELS por fases e parcelas;
- manifesto e validação automática do catálogo;
- auditorias reproduzíveis e workflow de qualidade.
- envelope rastreável de momento, cortante e deslocamento por combinação.
- catálogo controlado da NBR 8681:2025 com classificações independentes de
  `γq` e `ψ`, fatores das Tabelas 1 a 6 e bloqueio até a decisão `ND-001`.

### Changed

- aprovação global agora é bloqueada por pendências obrigatórias;
- evidência externa não é convertida em resultado do programa;
- dupla simetria deve ser declarada e fundamentada;
- triagem geométrica de enrijecedor não libera aumento de resistência.
- rotinas antigas e sem chamadas de esforços, flecha, `Cb`, FLT, FLM, FLA,
  cisalhamento e memorial foram removidas do Streamlit;
- versão do motor centralizada e elevada para `0.3.0`.
- memorial compatível com a sintaxe de `f-string` do Python 3.11 e campanha
  experimental do Mutmut 3.6 configurada no `pyproject.toml`.

### Known limitations

- NBR 8681:2025 integral disponível, mas ainda sem decisão de compatibilidade
  com a NBR 8800:2024; erratas e versões corrigidas requeridas continuam ausentes;
- catálogo atual está `INVALID_CATALOG_DATA`;
- a interface ainda usa adaptadores de compatibilidade para o núcleo de cálculo;
- não há revisão estrutural independente nem golden cases assinados.
