# Relatório de validação

## Classificação

**NÃO VALIDADO**

Data da execução: 2026-07-29  
Commit-base: `ab68c099e53a1f26974fd2adcbe752b0d4c8a6ec`  
Versão do motor: `0.3.0`

Esta classificação é obrigatória porque faltam erratas e versões corrigidas
requeridas, decisão de compatibilidade normativa, evidência independente,
rastreabilidade oficial do catálogo e atendimento das metas de teste. Aprovação
da suíte não substitui revisão de engenheiro habilitado.

## Verificações executadas

| Verificação | Resultado |
|---|---|
| testes | 178 aprovados |
| cobertura com branches | 90,06 %; `checks.flexure` em 100 %; meta global de 95 % não atingida |
| Ruff | aprovado no pacote, scripts e testes |
| mypy | aprovado em 24 módulos do pacote |
| determinismo | hash `7f147faeb25bfb590d0fdc4c39813da8c7a33ab80a022105006f850d65483ba7` |
| manifesto | quatro documentos registrados; estado `NORMATIVE_REVIEW_REQUIRED` |
| catálogo | 560 linhas, 14 ocorrências; estado `INVALID_CATALOG_DATA` |
| mutação | 124 mutantes; 92 mortos; 32 sobreviventes; score 74,19 %; meta elevada não atingida |
| evidência independente | ausente |

## Critérios de aceite

| Critério | Estado | Evidência ou bloqueio |
|---|---|---|
| normas e erratas registradas | parcial | quatro normas estão registradas; as erratas/versões corrigidas requeridas de 8800, 6120 e 6123 não foram fornecidas |
| compatibilidade NBR 8800 × NBR 8681 revisada | não | confronto item a item registrado em `ND-001`; decisão e revisor ainda ausentes |
| nenhuma fórmula normativa duplicada | não demonstrado | duplicações sem uso foram removidas do Streamlit; adaptador e memorial ainda exigem migração integral |
| nenhuma constante normativa sem referência | não demonstrado | matriz cobre o núcleo novo; adaptador legado ainda requer inventário final |
| várias ações e envelope | sim no núcleo | regras de produção continuam bloqueadas |
| FLT, mesa comprimida e contenção por trecho | parcial | arquitetura e testes existem; integração completa e resistência das contenções faltam |
| modo manual seguro | sim quanto ao bloqueio | evidência externa não se converte em cálculo do programa |
| catálogo com origem e validações | não | validações existem; origem oficial e duplicidades faltam |
| testes independentes dos estados-limites | não | não há golden cases assinados |
| transições de regime testadas | sim para primitivas centralizadas | parâmetros completos ainda aguardam revisão |
| suíte passa em CI | sim | run `30478048679`: Python 3.11, Python 3.13 e job de mutação concluídos; sobreviventes de mutação continuam como pendência de qualidade |
| memorial integralmente rastreável | parcial | registro JSON da análise existe; resistências e memorial visual ainda não são reconstruídos integralmente |
| revisão independente | não | profissional não designado |
| limitações declaradas | sim | `ASSUMPTIONS_AND_LIMITATIONS.md` |

## Riscos residuais

1. Resultados de combinações de produção não podem ser alegados até a decisão
   `ND-001`; o catálogo NBR 8681:2025 está controlado, mas propositalmente bloqueado.
2. A expressão atribuída à Errata 1:2025 permanece bloqueada.
3. O catálogo atual não pode fundamentar aprovação executiva.
4. Os 32 mutantes sobreviventes da primitiva de flexão ainda exigem triagem.
5. Enrijecedores, soldas, contato, transferência e painéis extremos não possuem
   verificação completa.
6. O fluxo Streamlit ainda usa um adaptador monolítico para partes de resistência
   e ELS.
7. Nenhum resultado foi confrontado com memorial independente assinado ou
   software de referência identificado.

## Condição para mudança de classificação

A classificação somente pode ser revista após fornecimento e hash das erratas e
versões corrigidas faltantes, resolução documentada das questões abertas, catálogo
oficial rastreável, execução e triagem de testes de mutação, cobertura das metas,
golden cases independentes e revisão formal por engenheiro habilitado.
