# Auditoria normativa — vigas I/H — ABNT NBR 8800:2024

Data da revisão: 17/07/2026  
Referência primária: cópia fornecida pelo usuário da ABNT NBR 8800:2024, 293 páginas.  
Complemento vigente identificado: ABNT NBR 8800:2024/Er1:2025 — Errata 1, de 25/02/2025.

## Escopo declarado

O aplicativo dimensiona vigas prismáticas de aço, com seção I/H duplamente simétrica, laminada ou soldada, fletidas no eixo forte e submetidas a ações gravitacionais estáticas no plano da alma. O resultado é válido apenas quando todas as hipóteses declaradas na interface forem satisfeitas.

Não são calculados pelo módulo: barras com força axial, torção ou flexão biaxial; estabilidade global do edifício; ligações; vigas mistas; perfis formados a frio; incêndio; sismo; aberturas na alma; fadiga; vibração; empoçamento; pares de forças localizadas opostas; painel de alma de ligação; e projeto completo de enrijecedores locais. Quando alguma dessas situações é declarada, o resultado global não pode ser aprovado silenciosamente.

## Matriz de conformidade implementada

| Tema | Referência | Implementação |
|---|---|---|
| Materiais | 4.6.2.2.1 | Verifica `fy ≤ 450 MPa` e relação nominal `fu/fy ≥ 1,15`; a interface registra a confirmação dos requisitos de qualificação e valores medidos. |
| Combinações ELU | 4.8.7.2.1, Tabelas 1 e 2 | Separa permanentes, peso próprio do perfil e variável principal; coeficientes são identificados por categoria. |
| Combinações ELS | 4.8.7.3 | Rara, frequente, quase permanente e parcela variável, com ψ1/ψ2 por categoria. |
| Análise da viga | 4.10 | Solução elástica de primeira ordem por funções de singularidade para carga uniforme e uma força pontual combinadas na mesma seção. |
| Modelos de apoio | hipótese de cálculo | Biapoiada, balanço, biengastada e engastada-apoiada, incluindo carga pontual excêntrica. |
| Flexão | 5.4.2 e Anexo D | FLT, FLM, FLA, limite geral `1,50 W fy/γa1`, contenção contínua e `Cb` no trecho destravado. |
| Alma esbelta | Anexo E | Perfis soldados dentro dos limites de aplicabilidade, com `kpg` e resistências próprias do Anexo E. |
| Furos na mesa tracionada | 5.4.2.6 | Verifica a condição com `Afn/Afg` e aplica o limite por ruptura quando necessário. |
| Cisalhamento | 5.4.3.1 | Usa a altura livre correta da alma (`d′` em laminados), `kv = 5,34` sem enrijecedores eficazes e os três regimes de resistência. |
| Enrijecedores de cisalhamento | 5.4.3.1.3 e Er1:2025 | Soldagem, esbeltez, inércia no plano médio da alma e expressão corrigida `j = 2,5/(a/h)² − 2 ≥ 0,5`. Enrijecedor inválido não aumenta `kv`. |
| Forças localizadas | 5.7.3 a 5.7.5 | Escoamento local, enrugamento e flambagem lateral da alma nos apoios e na força pontual de compressão. |
| Apoios sem restrição torcional | 5.7.8 | A condição é perguntada; a ausência de enrijecedores/restrição gera pendência normativa. |
| Flecha | Anexo B | Limites L/250, L/350 e L/500; em balanço, `L` é o dobro do comprimento teórico; limite adicional de 15 mm para alvenaria solidarizada. |
| Memorial | rastreabilidade | Mostra ações, combinação, reações, esforços, `Cb`, resistências, regimes, forças localizadas, ELS, hipóteses, pendências e status global. |

## Correções realizadas sobre o projeto original

- atualização da identificação normativa e inclusão explícita da Errata 1:2025;
- motor de cálculo isolado da interface em `calculos_nbr8800_2024.py`;
- eliminação da soma incorreta de máximos isolados e inclusão das cargas pontuais nos quatro modelos de apoio;
- inclusão do peso próprio específico de cada perfil;
- uso correto de `h`/`d′` da planilha e correção de `kv`;
- inclusão do Anexo E, limite geral de flexão e ruptura da mesa com furos;
- cálculo e validação geométrica dos enrijecedores de cisalhamento;
- verificações locais nos apoios e nas forças concentradas;
- combinação de serviço e limites do Anexo B;
- estado global em três níveis: `APROVADO`, `REPROVADO` e `NÃO VERIFICADO`;
- limite estrito de aprovação em 100,0 %, sem tolerância normativa inventada;
- memorial detalhado e testes automatizados de regressão.

## Limitações e responsabilidade técnica

As propriedades de `perfis.xlsx` não contêm metadados de fabricante, edição do catálogo ou tolerâncias. Devem ser conferidas com o certificado e o catálogo adotados no projeto executivo. As ações características ainda dependem das normas de ações aplicáveis ao empreendimento, como ABNT NBR 6120, ABNT NBR 6123 e ABNT NBR 8681.

O software é ferramenta de auxílio e não substitui a modelagem completa, o detalhamento, a avaliação das condições reais de contenção e a responsabilidade do engenheiro legalmente habilitado.

## Validação executada

- compilação dos módulos Python;
- 20 testes automatizados cobrindo esforços, reações e flechas dos quatro vínculos, carga pontual excêntrica, `Cb`, limites de material, Anexo E, limite de flexão, furos, `kv`, Errata 1 e inércia dos enrijecedores;
- análise em lote e teste de integração dos 560 perfis das quatro famílias da planilha;
- geração e inspeção do memorial no navegador;
- auditoria textual para referências normativas obsoletas, tolerâncias indevidas e numeração antiga de tabelas.

## Fontes complementares

- CBCA — lançamento da ABNT NBR 8800:2024: https://www.cbca-acobrasil.org.br/site/noticia/lancamento-da-abnt-nbr-8800-2024
- CBCA — biblioteca e manual *Uso Fácil — ABNT NBR 8800:2024*: https://cbca-acobrasil.org.br/site/biblioteca
- Registro bibliográfico da Errata 1:2025: https://www.dinmedia.de/en/standard/abnt-nbr-8800-errata-1/390520685
