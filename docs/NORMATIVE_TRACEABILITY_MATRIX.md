# Matriz de rastreabilidade normativa

## Legenda

- `BASELINE_IMPLEMENTED_UNVERIFIED`: existe código, mas a transcrição e a aplicabilidade ainda não
  foram verificadas com evidência controlada.
- `NORMATIVE_REVIEW_REQUIRED`: falta fonte integral, decisão normativa ou revisão.
- `PARTIAL_IMPLEMENTATION`: barreira de segurança implementada, mas o requisito completo ainda
  possui trabalho ou evidência pendente.
- `NOT_IMPLEMENTED`: funcionalidade ausente.
- `OUT_OF_SCOPE`: funcionalidade deliberadamente excluída, com bloqueio de aprovação quando
  aplicável.
- `INDEPENDENT_EVIDENCE_REQUIRED`: falta resultado de referência independente.

| Requisito | Norma/item | Aplicabilidade | Implementação | Arquivo/função | Teste | Evidência independente | Status | Revisor |
|---|---|---|---|---|---|---|---|---|
| limites de material do escopo | NBR 8800:2024, item alegado 4.6.2.2.1 | aço estrutural informado | valida fy e fu | `calculos_nbr8800_2024.validate_material` | `test_material_limits` | ausente | BASELINE_IMPLEMENTED_UNVERIFIED | não designado |
| classificação completa de ações | NBR 8681:2025; NBR 8800:2024, 4.8 | todo modo automático | classes tipadas existem; categorias de produção não foram cadastradas | `domain.actions`, `combine_elu_normal`, `combine_els`, UI | domínio e rejeição de categoria sem regra | ausente | NORMATIVE_REVIEW_REQUIRED | não designado |
| ELU normal com variável principal alternada | NBR 8681:2025; NBR 8800:2024, 4.8.7.2.1 | múltiplas ações variáveis | mecanismo genérico dirigido por regras externas; sem coeficientes de produção | `combinations.generate_combinations` | regras sintéticas `TEST_ONLY` | ausente | PARTIAL_IMPLEMENTATION | não designado |
| ELU especial, construção e excepcional | NBR 8681:2025; NBR 8800:2024, 4.8.7.2.2 a 4.8.7.2.4 | quando solicitado | não implementado | futuro `combinations` | ausente | ausente | NOT_IMPLEMENTED | não designado |
| ELS quase permanente, frequente e rara | NBR 8681:2025; NBR 8800:2024, 4.8.7.3 | ELS | mecanismo genérico disponível; regras de produção bloqueadas | `combine_els`, `combinations.generate_combinations` | fatores sintéticos e baseline | ausente | NORMATIVE_REVIEW_REQUIRED | não designado |
| ações de uso/ocupação | NBR 6120:2019 corrigida | quando inseridas | número livre sem categoria controlada | UI | ausente | ausente | NORMATIVE_REVIEW_REQUIRED | não designado |
| vento | NBR 6123:2023 corrigida/Er1:2025 | quando houver vento | não implementado | nenhum | ausente | ausente | OUT_OF_SCOPE | não designado |
| análise de q uniforme total | modelo elástico e NBR 8800:2024, 4.10 | viga prismática de um vão | solver genérico para quatro vínculos; motor legado ainda ativo na UI | `analysis.analyze_prismatic_beam`, `analyze_beam` | soluções clássicas dos quatro vínculos | sem relatório assinado | INDEPENDENT_EVIDENCE_REQUIRED | não designado |
| carga uniforme parcial | modelo estrutural | quando houver | solver genérico implementado, ainda não integrado à UI | `analysis.analyze_prismatic_beam` | equilíbrio e reações independentes | ausente | PARTIAL_IMPLEMENTATION | não designado |
| carga linearmente variável | modelo estrutural | quando houver | solver genérico implementado, ainda não integrado à UI | `analysis.analyze_prismatic_beam` | resultante triangular independente | ausente | PARTIAL_IMPLEMENTATION | não designado |
| várias forças pontuais | modelo estrutural | quando houver | solver genérico implementado, ainda não integrado à UI | `analysis.analyze_prismatic_beam` | equilíbrio com duas forças | ausente | PARTIAL_IMPLEMENTATION | não designado |
| momentos aplicados | modelo estrutural | quando houver | solver genérico implementado, ainda não integrado à UI | `analysis.analyze_prismatic_beam` | salto de momento | ausente | PARTIAL_IMPLEMENTATION | não designado |
| extremos de M e V | modelo estrutural | modelo atual | M analítico; V por candidatos | `analyze_beam` | parcial | ausente | INDEPENDENT_EVIDENCE_REQUIRED | não designado |
| extremo de deslocamento | modelo estrutural | quando E e I informados | raízes da rotação por elemento e refinamento com erro no solver novo; UI ainda usa malha fixa | `analysis.analyze_prismatic_beam`, `analyze_beam` | raízes, tolerância e não convergência | ausente | PARTIAL_IMPLEMENTATION | não designado |
| Cb por trecho | NBR 8800:2024, 5.4.2.3 a 5.4.2.5 | FLT | um único trecho | `calculate_cb`, `perform_all_checks` | q uniforme | ausente | BASELINE_IMPLEMENTED_UNVERIFIED | não designado |
| FLT por todos os segmentos | NBR 8800:2024, 5.4.2 | viga com contenções | não implementado | nenhum | ausente | ausente | NOT_IMPLEMENTED | não designado |
| mesa comprimida por segmento | NBR 8800:2024, 5.4.2 | FLT | não implementado | nenhum | ausente | ausente | NOT_IMPLEMENTED | não designado |
| contenção lateral/torcional/empenamento por segmento e mesa | NBR 8800:2024, 4.12 e 5.4.2 | FLT | checkbox global | UI | ausente | ausente | NOT_IMPLEMENTED | não designado |
| limite global de flexão | NBR 8800:2024, 5.4.2.2 | análise elástica | implementado | `_overall_flexural_cap` | limite superior | ausente | BASELINE_IMPLEMENTED_UNVERIFIED | não designado |
| FLT, FLM e FLA de alma não esbelta | NBR 8800:2024, Anexo D | I/H duplamente simétrico | função monolítica | `flexural_strength_i` | casos isolados | ausente | BASELINE_IMPLEMENTED_UNVERIFIED | não designado |
| alma esbelta | NBR 8800:2024, Anexo E | perfil soldado dentro dos limites | implementado com hipóteses implícitas | `flexural_strength_i` | um caso positivo | ausente | BASELINE_IMPLEMENTED_UNVERIFIED | não designado |
| furos na mesa tracionada | NBR 8800:2024, item alegado 5.4.2.6 | quando há furos | razão Afn/Afg informada | `flexural_strength_i` | um caso governante | ausente | BASELINE_IMPLEMENTED_UNVERIFIED | não designado |
| cisalhamento da alma | NBR 8800:2024, 5.4.3.1 | I/H | três regimes | `shear_strength_i` | casos pontuais | ausente | BASELINE_IMPLEMENTED_UNVERIFIED | não designado |
| expressão corrigida de j | NBR 8800:2024/Er1:2025 | enrijecedor transversal | código alega correção | `shear_strength_i` | repete expressão | cópia da errata ausente | NORMATIVE_REVIEW_REQUIRED | não designado |
| resistência completa de enrijecedores e soldas | NBR 8800:2024, itens aplicáveis | quando enrijecedor necessário | somente triagem geométrica parcial | `shear_strength_i` | inércia e esbeltez | ausente | NOT_IMPLEMENTED | não designado |
| forças localizadas de compressão | NBR 8800:2024, 5.7.3 a 5.7.5 | apoio/carga de compressão | três resistências em uma função | `local_compression_strength` | integração de catálogo | ausente | BASELINE_IMPLEMENTED_UNVERIFIED | não designado |
| flexão local da mesa | NBR 8800:2024, 5.7.2 | força transversal aplicável | função órfã | `local_flange_bending_strength` | ausente | ausente | NOT_IMPLEMENTED | não designado |
| matriz por tipo de força localizada | NBR 8800:2024, 5.7 | todo caso aplicável | não existe | nenhum | ausente | ausente | NOT_IMPLEMENTED | não designado |
| ELS por fase/parcela | NBR 8800:2024, Anexo B; NBR 8681:2025 | elemento sensível | flecha total simplificada | `combine_els`, `deflection_limit` | limite de balanço | ausente | NORMATIVE_REVIEW_REQUIRED | não designado |
| vibração | NBR 8800:2024, Anexo I | quando aplicável | triagem textual | UI | ausente | ausente | OUT_OF_SCOPE | não designado |
| catálogo rastreável | catálogo oficial de cada fabricante/família | todos os perfis | planilha sem metadados | `perfis.xlsx` | executabilidade | ausente | NORMATIVE_REVIEW_REQUIRED | não designado |
| evidência externa manual | política de auditoria | modo manual | modelo tipado, upload PDF, SHA-256 e identificação; resultados externos ainda não são importados | `ExternalEvidence`, UI e `perform_all_checks` | rastreabilidade e bloqueio | ausente | PARTIAL_IMPLEMENTATION | não designado |
| status global seguro | política de auditoria | todas as verificações | enum e agregador novos; ponte legada bloqueia N/A e usa frase de escopo | `domain.status`, `overall_status` | bloqueadores, N/A e não aplicabilidade | ausente | PARTIAL_IMPLEMENTATION | não designado |
| memorial reproduzível por JSON | política de auditoria | toda análise | HTML dependente da sessão | memorial/UI | testes textuais | ausente | NOT_IMPLEMENTED | não designado |
