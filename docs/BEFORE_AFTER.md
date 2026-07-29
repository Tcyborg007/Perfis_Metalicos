# Comparação entre o commit-base e a branch de auditoria

| Aspecto | Commit-base `ab68c099` | Branch auditada |
|---|---|---|
| suíte | 40 testes | 179 testes |
| cobertura | 59 % no conjunto medido do baseline | 90,06 % com branches no pacote novo; `checks.flexure` em 100 % |
| estrutura | módulos de topo e Streamlit com rotinas duplicadas | pacote `src/perfis_metalicos` separado por domínio, combinações, análise, verificações, catálogo e auditoria |
| ações | modelo simplificado | ações tipadas, gerador genérico e catálogo NBR 8681:2025 em duas classificações (`γq` e `ψ`); produção bloqueada até `ND-001` |
| análise | carga uniforme e uma força pontual | carga uniforme total/parcial, linear, múltiplos pontos, momentos e refinamento controlado |
| envelope | ausente | extremos associados à combinação e posição; não convergência bloqueia |
| FLT | um `Cb` global | segmentos com `Lb`, momentos, `Cb`, mesa comprimida, contenções, resistência e utilização próprios |
| mesa contida | seleção global podia afastar FLT | classificação por mesa/segmento e caminhos explícitos de 5.4.2.4 |
| modo manual | declaração do usuário podia encerrar verificação | evidência tipada com metadados e hash; pendência não vira resultado do programa |
| catálogo | planilha aceita diretamente | manifesto, hash, coerências e bloqueio `INVALID_CATALOG_DATA` |
| status | textos permissivos | enum tipado; pendência obrigatória impede aprovação |
| reprodutibilidade | sessão Streamlit | JSON canônico com hashes, versão, commit, escopo e pendências |
| CI | inexistente | Python 3.11/3.13, lock, Ruff, mypy, testes, cobertura e auditorias |
| mutação | inexistente | campanha crítica de flexão: 124/124 mortos (100 %); demais módulos ainda sem score |

## Resultado

As mudanças foram separadas em commits temáticos a partir do commit-base. O
avanço de engenharia é significativo, mas não transforma a branch em software
validado: as fontes normativas faltantes, o catálogo sem origem oficial, a
cobertura abaixo da meta, a mutação não triada e a ausência de revisão
independente continuam bloqueantes.
