# Auditoria de baseline

## 1. Identificação e conclusão do baseline

| Campo | Valor |
|---|---|
| Repositório | `Tcyborg007/Perfis_Metalicos` |
| Commit-base solicitado e auditado | `ab68c099e53a1f26974fd2adcbe752b0d4c8a6ec` |
| Data do commit | 2026-07-21T20:43:36-03:00 |
| Data desta auditoria | 2026-07-29 |
| Ambiente observado | Windows; Python 3.13.5; pip 26.0.1 |
| Classificação do baseline | **NÃO VALIDADO** |

Esta classificação não afirma que todos os resultados estejam incorretos. Ela significa que o
baseline não reúne as evidências necessárias para demonstrar conformidade verificável: faltam
manifesto normativo, rastreabilidade requisito–código–teste, casos independentes de referência,
validação da fonte do catálogo, estados de verificação seguros, cobertura suficiente das rotinas
críticas e revisão independente por engenheiro habilitado.

Nenhuma equação de cálculo foi modificada durante esta etapa. Este documento é o primeiro
artefato da auditoria e constitui o portão obrigatório antes de qualquer alteração normativa.

## 2. Método da auditoria inicial

Foram executados:

1. inventário dos arquivos versionados no commit-base;
2. leitura estática dos módulos Python e da documentação existente;
3. extração por AST de funções, chamadas e literais numéricos;
4. rastreamento das importações e dos pontos de entrada;
5. procura de rotinas sem referências e de fórmulas duplicadas;
6. execução da suíte pelos dois comandos compatíveis com o projeto;
7. compilação dos módulos;
8. medição de cobertura de linhas e de branches;
9. inspeção estrutural básica da planilha de perfis.

As referências normativas existentes no código ainda não foram aceitas como evidência. Nesta
etapa elas são registradas como alegações do baseline. A confirmação item a item será feita na
etapa de manifesto e rastreabilidade, exclusivamente com cópias legalmente fornecidas.

## 3. Inventário do repositório

| Arquivo | Bytes | Linhas de texto | Papel observado |
|---|---:|---:|---|
| `.devcontainer/devcontainer.json` | 1.046 | 33 | ambiente de desenvolvimento |
| `.gitignore` | 100 | 9 | exclusões do Git |
| `.streamlit/config.toml` | 227 | 11 | tema e servidor Streamlit |
| `AUDITORIA_NBR8800_2024.md` | 5.820 | 50 | auditoria anterior, não suficiente como evidência de validação |
| `Dockerfile` | 319 | 9 | imagem de execução |
| `README.md` | 954 | 17 | instruções mínimas de execução |
| `app.py` | 142 | 4 | ponto de entrada Streamlit |
| `calculos_nbr8800_2024.py` | 31.178 | 777 | núcleo de cálculo ativo |
| `main.py` | 164.811 | 2.798 | interface, orquestração e código estrutural legado |
| `memorial_diagrams.py` | 25.762 | 467 | diagramas SVG/HTML |
| `memorial_nbr8800_2024.py` | 108.104 | 1.468 | memorial e reprodução textual de equações |
| `perfis.xlsx` | 183.547 | binário | catálogo de 560 registros |
| `requirements.txt` | 58 | 6 | dependências, parcialmente não fixadas |
| `tests/test_memorial_detailed.py` | 16.637 | 308 | testes de memorial e diagramas |
| `tests/test_nbr8800_2024.py` | 10.081 | 216 | testes do núcleo |
| `tests/test_profile_catalog_integration.py` | 2.425 | 58 | teste de execução do catálogo |
| `tests/test_streamlit_layout.py` | 3.296 | 65 | testes estáticos de interface |

Ausências relevantes no baseline:

- não há `pyproject.toml`;
- não há arquivo de lock;
- não há workflow em `.github/workflows`;
- não há configuração de tipagem estática, lint, coverage mínimo, mutation testing ou pre-commit;
- não há pacote `src/perfis_metalicos`;
- não há manifesto normativo ou matriz formal de rastreabilidade.

## 4. Resultado original dos testes

| Verificação | Resultado |
|---|---|
| `python -m pytest -q tests` | **40 passed in 3.82s** |
| `python -m unittest discover -s tests -v` | **40 testes, OK, 1.362s** |
| `python -m py_compile ...` nos cinco módulos | **sem erro** |

O resultado acima é preservado como fotografia de regressão. Ele não é evidência suficiente de
correção normativa. O arquivo `AUDITORIA_NBR8800_2024.md` afirma “20 testes”, portanto está
desatualizado em relação ao commit-base.

### 4.1 Cobertura do baseline

Medição: `coverage run --branch -m pytest -q tests`.

| Módulo | Statements | Miss | Branches | Branches parciais | Cobertura |
|---|---:|---:|---:|---:|---:|
| `calculos_nbr8800_2024.py` | 422 | 36 | 134 | 31 | 88% |
| `main.py` | 1.075 | 893 | 312 | 11 | 16% |
| `memorial_diagrams.py` | 215 | 6 | 60 | 10 | 94% |
| `memorial_nbr8800_2024.py` | 465 | 49 | 150 | 26 | 86% |
| Total, incluindo testes | 2.564 | 989 | 692 | 83 | **59%** |

Não existe baseline de mutation score. Não existe comprovação de 100% de branch coverage nas
funções normativas críticas nem de 95% no núcleo.

## 5. Fluxo completo observado

```text
app.py
  └─ main.main()
       ├─ Streamlit coleta geometria, material, vínculos, ações e hipóteses
       ├─ load_data_from_local_file() lê perfis.xlsx
       ├─ get_profile_properties() converte dimensões mm → cm
       ├─ run_detailed_analysis() ou run_batch_analysis()
       │    └─ perform_all_checks()
       │         ├─ modo automático
       │         │    ├─ combine_elu_normal()
       │         │    ├─ analyze_beam() → Msd, Vsd, reações e diagramas
       │         │    ├─ calculate_cb() em um único trecho informado
       │         │    ├─ combine_els()
       │         │    └─ analyze_beam() → deslocamentos
       │         ├─ modo manual
       │         │    └─ recebe apenas Msd e Vsd; não calcula ELS nem forças locais
       │         ├─ flexural_strength_i()
       │         ├─ shear_strength_i()
       │         ├─ local_compression_strength() por apoio/carga, se automático
       │         ├─ deflection_limit(), se houver resposta ELS
       │         ├─ _verification_status()
       │         └─ overall_status()
       └─ build_memorial_details()
            ├─ memorial_nbr8800_2024.py recompõe equações em LaTeX/HTML
            └─ memorial_diagrams.py gera representações SVG
```

### 5.1 Política de unidades observada

O núcleo declara `kN` e `cm`, com tensões e módulo de elasticidade em `kN/cm²`. A interface:

- lê `d`, `bf`, `tw`, `tf`, `h` e `d'` em milímetros e divide por `10`;
- mantém propriedades de área/seção/inércia em `cm²`, `cm³`, `cm⁴` e `cm⁶`;
- converte ação de área em ação linear usando largura de influência em metros;
- converte massa linear em força por comprimento com `9,80665/100000`;
- converte momentos entre `kN·cm` e `kN·m` em diversos pontos usando `100`.

Essas conversões são implícitas em dicionários genéricos. Não há tipos dimensionais, metadados de
unidade nos resultados críticos ou barreira de tipo contra mistura de `mm`, `cm`, `m`, `kN·cm` e
`kN·m`.

## 6. Funções que implementam ou reproduzem equações estruturais

### 6.1 Núcleo ativo

| Arquivo/função | Linhas | Responsabilidade | Situação do baseline |
|---|---:|---|---|
| `BeamResponse.moment_at` | 54–62 | momento por função de singularidade | ativa |
| `_beam_end_actions` | 74–102 | reações e momentos de extremidade para quatro vínculos | ativa |
| `analyze_beam` | 105–208 | M, V e deslocamento para q uniforme + uma força pontual | ativa; flecha máxima por malha fixa |
| `calculate_cb` | 211–253 | Cb de um único trecho | ativa; não há envelope por segmentos |
| `combine_elu_normal` | 256–282 | ELU normal com uma variável | ativa; explicitamente simplificada |
| `combine_els` | 285–327 | quatro opções ELS com uma variável | ativa; explicitamente simplificada |
| `_overall_flexural_cap` | 341–342 | limite global de flexão | ativa |
| `_piecewise_strength` | 345–359 | interpolação por regimes | ativa |
| `flexural_strength_i` | 362–590 | FLT, FLM, FLA/Anexo E e furos | ativa; 229 linhas e múltiplas responsabilidades |
| `shear_strength_i` | 593–685 | resistência ao cisalhamento e triagem geométrica de enrijecedores | ativa |
| `local_compression_strength` | 688–810 | estados locais sob compressão transversal | ativa |
| `local_flange_bending_strength` | 813–819 | flexão local da mesa | **sem qualquer referência de chamada** |
| `deflection_limit` | 822–833 | limite geométrico de deslocamento | ativa |
| `overall_status` | 836–846 | agregação de estados | ativa e crítica à segurança |

### 6.2 Rotinas estruturais antigas em `main.py`

As funções abaixo não possuem referência de chamada no código ou nos testes do baseline:

| Função | Linhas | Duplicação |
|---|---:|---|
| `calcular_esforcos_viga` | 711–774 | análise de viga |
| `calcular_cb` | 776–858 | Cb |
| `calcular_flecha_maxima` | 860–914 | flecha |
| `_calcular_mrdx_flt` | 951–1127 | FLT |
| `_calcular_mrdx_flm` | 1129–1308 | FLM |
| `_calcular_mrdx_fla` | 1310–1434 | FLA |
| `_calcular_vrd` | 1436–1524 | cisalhamento |
| `_render_cb_calc_section` | 1822–1872 | reprodução antiga do Cb |
| `_render_esforcos_viga_section` | 1874–1996 | reprodução antiga de esforços |
| `_memorial_2024_html_legacy_summary` | 2007–2114 | memorial legado |
| `build_step_by_step_html` | 2350–2400 | memorial legado |

Também não têm chamada `_build_verification_block_html` fora de renderizadores legados, e
`Config` duplica coeficientes que já existem no núcleo. A remoção dessas rotinas exige primeiro
testes de caracterização e registro explícito de divergências, conforme o plano da auditoria.

### 6.3 Equações reproduzidas no memorial

`memorial_nbr8800_2024.py` não deve decidir resistências, mas recompõe manualmente fórmulas,
coeficientes, conversões e decisões em `_beam_actions`, `_cb_section`, `_flexure_section`,
`_annex_e_step`, `_shear_section`, `_local_section` e `_els_section`. Essa reprodução é uma
duplicação semântica: mudanças no motor podem não ser refletidas no memorial. O modelo futuro
deve receber evidências e etapas estruturadas do núcleo, sem reimplementar fórmulas.

## 7. Funções duplicadas, antigas ou não utilizadas

### 7.1 Confirmadas por análise estática

- 11 rotinas legadas listadas em 6.2 não têm chamada.
- `local_flange_bending_strength()` não é chamada.
- `_esc()` existe separadamente em `memorial_nbr8800_2024.py` e
  `memorial_diagrams.py`; é duplicação utilitária, não normativa.
- `Config` repete `GAMMA_A1` e diversos coeficientes de resistência presentes no núcleo.
- fórmulas de análise, Cb, FLT, FLM, FLA, cisalhamento e flecha aparecem simultaneamente no
  núcleo ativo, no código legado de `main.py` e como texto calculado no memorial.

### 7.2 Risco de divergência já observável

- o núcleo limita o escopo a q uniforme e uma força pontual; as rotinas legadas possuem casos
  incompletos e caminhos distintos;
- a UI contém listas textuais de coeficientes e fatores, e o núcleo recebe números sem categoria
  normativa tipada;
- o memorial usa seus próprios literais e conversões, em vez de serializar uma trilha de cálculo
  produzida pelo motor.

## 8. Censo e classificação das constantes numéricas

### 8.1 Escopo do censo

O censo por AST encontrou:

| Módulo | Ocorrências | Valores únicos |
|---|---:|---:|
| `calculos_nbr8800_2024.py` | 276 | 58 |
| `main.py` | 542 | 70 |
| `memorial_nbr8800_2024.py` | 278 | 15 |
| `memorial_diagrams.py` | 181 | 48 |

Literais em testes são dados de ensaio, não constantes de produção. Números dentro de strings de
CSS, HTML, textos de seleção e LaTeX não são detectados como literais Python; eles foram
inspecionados separadamente quando afetam cálculo ou seleção normativa. Os números puramente
gráficos de SVG/CSS são classificados como interface.

“Normativa” abaixo significa **apresentada pelo baseline como normativa**, ainda não confirmada
contra a cópia controlada da norma.

### 8.2 Normativas alegadas

| Grupo | Valores e local principal | Observação |
|---|---|---|
| coeficientes de resistência | `1,10`, `1,35` — núcleo linhas 17–18; duplicados em `main.py` | sem manifesto ou item associado ao símbolo |
| Cb | `2,5`, `3`, `4`, `12,5` — `calculate_cb`; repetidos em legado e memorial | fórmula alegada como 5.4.2.3-a |
| combinações ELU | defaults `1,50`, `1,50`, `1,25` — `combine_elu_normal`; opções textuais `1,50`, `1,40`, `1,35`, `1,30`, `1,25`, `1,20` na UI | apenas uma variável; categoria não é tipo de domínio |
| combinações ELS | `1,0`, `0,6`, `0,4`; opções de ψ `0,8`, `0,7`, `0,6`, `0,5`, `0,4`, `0,3` | valores selecionados na UI e passados sem origem estruturada |
| limites de material | `45`, `1,15` — `validate_material` | alegados como 450 MPa e relação fu/fy |
| flexão/FLT/FLM/FLA/Anexo E | `0,039`, `0,30`, `0,35`, `0,38`, `0,40`, `0,42`, `0,49`, `0,69`, `0,76`, `0,80`, `0,83`, `0,90`, `0,95`, `1,00`, `1,10`, `1,40`, `1,50`, `2`, `3`, `3,76`, `4`, `5,70`, `6`, `10`, `11,7`, `12`, `260`, `300`, `1200`, `π` | concentrados em `flexural_strength_i`; referências exatas ainda não auditadas |
| cisalhamento/enrijecedores | `0,50`, `0,56`, `0,60`, `1,10`, `1,24`, `1,37`, `2`, `2,5`, `3`, `5`, `5,34`, `12` | `shear_strength_i`; expressão de `j` declara Errata 1:2025 |
| forças localizadas | `0,20`, `0,33`, `0,37`, `0,66`, `0,94`, `1`, `1,10`, `1,5`, `1,7`, `2`, `2,3`, `2,5`, `3`, `4`, `5`, `5,70`, `16`, `32`, `300`, `1200` | `local_compression_strength`; exige matriz de aplicabilidade |
| flexão local da mesa | `6,25`, `10`, `0,5` | função não integrada; origem ainda não verificada |
| deslocamento | multiplicador `2` para balanço; divisores `250`, `350`, `500`; limite `1,5 cm` | seleção simplificada da UI; origem e parcela de deslocamento não estruturadas |

### 8.3 Físicas ou dados de material

| Valor | Local | Classificação |
|---:|---|---|
| `9,80665 m/s²` | conversão de massa linear em peso próprio, `perform_all_checks` | física |
| `20.000 kN/cm²` | valor inicial de E na UI | física/material, mas editável |
| pares `34,5/45` e `25/40 kN/cm²` | presets A572 Gr 50 e A36 | material; requer fonte e faixa de espessura |

### 8.4 Geométricas, mecânicas e de conversão de unidade

| Grupo | Valores | Local |
|---|---|---|
| equilíbrio e compatibilidade dos quatro vínculos | `2`, `3`, `5`, `8`, `12` | `_beam_end_actions` |
| integrações de M/EI | `2`, `3`, `4`, `6`, `24` | `analyze_beam` e `BeamResponse` |
| fórmulas clássicas legadas de flecha | `3`, `5`, `8`, `12`, `185`, `384` | rotina não utilizada `calcular_flecha_maxima` |
| quartos do trecho | `0,25`, `0,50`, `0,75`, `4` | Cb, legado e diagramas |
| conversões | `10` (mm→cm), `100` (cm↔m e kN·cm↔kN·m), `100.000` (kg/m→kN/cm com g) | interface/orquestração |
| largura de influência | divisor `200` | soma de duas meias larguras em cm para largura tributária em m |

O valor `185` da rotina legada de flecha não possui referência ou derivação no repositório e,
por isso, também integra a classe “sem origem identificada” até caracterização.

### 8.5 Numéricas

| Valores | Uso |
|---|---|
| `1e-9`, `1e-12` | tolerâncias locais e proteção de comparações; não há política única |
| `101`, `2001`, `4001` em teste | tamanho mínimo, malha default e contraste de malhas |
| `181` | amostragem de curvas SVG |
| `3`, `4` | precisão padrão de formatadores |
| `0` e `1` | sentinelas, valores neutros, índices e controles de fluxo |

A flecha máxima do motor usa a malha fixa de 2.001 pontos. Não existe estimativa de erro,
resolução de rotação nula por trecho ou refinamento adaptativo.

### 8.6 Interface

Constantes de interface incluem:

- limites, valores iniciais e passos de campos Streamlit: `0`, `0,01`, `0,05`, `0,1`, `0,25`,
  `0,5`, `0,8`, `0,85`, `1`, `3`, `10`, `50`, `80`, `100`, `200`, `350`, `500`, `1.000`,
  `9.000`;
- limites e faixas de gráficos: `14`, `15`, `20`, `55`, `70`, `80`, `95`, `100`, `150`,
  `500`;
- geometria SVG: `0,14`, `0,25`, `0,45`, `0,5`, `0,75`, `1`, `2`, `3`, `4`, `5`, `7`,
  `9`, `10`, `12`, `13`, `14`, `18`, `23`, `25`, `27`, `28`, `31`, `32`, `36`, `38`,
  `39`, `42`, `58`, `78`, `100`, `101`, `120`, `121`, `126`, `135`, `180`, `181`,
  `218`, `232`, `276`, `286`, `560`, `585`, `682`, `720`.

Esses valores não devem influenciar o resultado estrutural. A separação atual não impede
completamente essa mistura porque interface e orquestração permanecem no mesmo arquivo.

### 8.7 Sem origem identificada ou sem rastreabilidade suficiente

- todos os coeficientes “normativos alegados” permanecem sem confirmação controlada até a matriz
  de rastreabilidade;
- `1,76`, `1,38` e `27` na rotina legada `_calcular_mrdx_flt`;
- `185` na rotina legada de flecha;
- defaults de comprimentos de apoio, espaçamento/dimensões de enrijecedores e posições de carga
  são escolhas de interface, mas não são marcados como exemplo ou projeto;
- as 560 linhas de `perfis.xlsx` não possuem fabricante, catálogo, edição, página, hash de fonte,
  tolerâncias ou revisor.

## 9. Catálogo no baseline

SHA-256 de `perfis.xlsx`:
`EB95CEA376935EF62C8B9C311E0BB8BD72A80EE65BC69811E87CB2C8D2C08001`.

| Aba | Registros | Colunas | Duplicidades de designação na própria aba |
|---|---:|---:|---:|
| Laminados | 107 | 20 | 0 |
| CS | 144 | 20 | 0 |
| CVS | 135 | 20 | 0 |
| VS | 174 | 20 | **5** |
| Total | **560** | — | **5** |

O teste existente apenas confirma que as rotinas retornam números finitos ou zero para os 560
registros. Ele não verifica coerência geométrica, massa, área, módulos, raios de giração,
duplicidades, unidades ou correspondência com catálogo oficial.

## 10. Achados e riscos priorizados

### Críticos

1. **Estado inseguro no modo manual.** A checkbox “Confirmo que forças localizadas e ELS foram
   verificados externamente” pode remover a pendência sem documento, responsável, registro
   profissional, revisão ou hash. O ELS fica `N/A`, e `overall_status()` aceita `N/A` junto de
   `APROVADO` como aprovação global.
2. **FLT não é verificada por todos os segmentos.** Existe apenas um `Lb`, um início de trecho e
   um Cb. O momento global `Msd` é comparado à resistência calculada com o Cb desse único trecho,
   permitindo associação entre demanda e trecho sem envelope segmentado.
3. **Desativação global da FLT.** Uma opção da UI define `flt_applicable=False` para toda a viga
   com base em declaração global de contenção contínua.
4. **Fonte do catálogo não validada.** O lote pode exibir aprovação para propriedade sem origem
   rastreável; há cinco designações duplicadas na família VS.
5. **Fórmulas duplicadas.** Núcleo, rotinas legadas e memorial contêm representações próprias das
   mesmas equações e coeficientes.

### Altos

1. combinações aceitam apenas uma ação variável e não geram variável principal alternada,
   acompanhantes, casos favoráveis/desfavoráveis ou envelope;
2. a análise aceita somente q uniforme em todo o vão e uma força pontual;
3. a flecha máxima é localizada por malha fixa;
4. estados são strings de três níveis e não distinguem `NOT_CHECKED`, `OUT_OF_SCOPE`,
   `INVALID_INPUT` e `EXTERNAL_EVIDENCE_REQUIRED`;
5. `flexural_strength_i()` agrega muitos regimes e hipóteses em um dicionário sem tipos;
6. o Anexo E adota `Wxc = W` no caminho ativo sem um tipo que imponha dupla simetria e sem
   evidência geométrica estruturada;
7. validação de enrijecedor é predominantemente geométrica; resistência axial, flambagem,
   transferência, soldas e contato não formam verificações independentes completas;
8. `local_flange_bending_strength()` existe, mas não integra a matriz de forças localizadas;
9. não há testes sistemáticos `λp±ε` e `λr±ε`, monotonicidade, dimensionalidade ou mutação.

### Médios

1. dependências não estão integralmente fixadas: somente Streamlit possui versão exata;
2. não há CI, lint, type checking, política de revisão ou determinismo;
3. `AUDITORIA_NBR8800_2024.md` mistura alegações de conformidade com testes internos e contém
   contagem desatualizada;
4. unidades e resultados críticos são transportados em dicionários de chaves livres;
5. referências normativas são strings no retorno ou no memorial, sem identidade de edição,
   errata, página, hash da cópia ou revisão.

## 11. Limitações dos testes atuais

- vários testes de resistência repetem a mesma expressão da implementação ou verificam apenas
  propriedades fracas, como positividade e presença de texto;
- o teste de catálogo é de executabilidade, não de validação da fonte;
- não há golden test com cálculo manual independente identificado;
- não há segundo algoritmo ou software de referência documentado;
- não há teste que impeça Cb de um trecho de ser aplicado a outro;
- não há teste de várias ações variáveis, cargas parciais, cargas lineares, vários pontos ou
  momentos aplicados;
- não há teste que proíba aprovação quando há pendência obrigatória;
- não há teste independente para todas as transições de regime;
- não há mutation testing.

## 12. Portão para a próxima etapa

Antes de alterar qualquer equação:

1. criar manifesto das normas e registrar quais cópias integrais estão legalmente disponíveis;
2. marcar `NORMATIVE_REVIEW_REQUIRED` onde a cópia integral não estiver disponível;
3. criar matriz inicial de rastreabilidade e lista de perguntas abertas;
4. registrar a incompatibilidade potencial entre referências internas do baseline e a
   NBR 8681:2025, sem escolher silenciosamente coeficientes;
5. obter aprovação humana para decisões normativas que não sejam mera transcrição verificável;
6. manter a classificação **NÃO VALIDADO** até que as evidências independentes e os critérios de
   aceite sejam satisfeitos.
