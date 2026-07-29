# Relatório de testes de mutação

## Estado

`PENDING_CI_EXECUTION`

O Mutmut 3.6.0 recusa execução nativa no Windows e o ambiente local não possui WSL nem Docker.
Nenhum mutation score foi inventado ou estimado.

O workflow Linux executa uma campanha inicial limitada a
`src/perfis_metalicos/checks/flexure.py`, usando
`tests/test_flexure_piecewise.py`, e publica `mutation-results.txt` como artefato.
Os caminhos são configurados em `[tool.mutmut]`, conforme a interface do Mutmut
3.6; a etapa de execução é experimental e seu resultado é registrado mesmo
quando há mutantes sobreviventes.

O job está marcado como experimental (`continue-on-error`) enquanto os mutantes equivalentes e
os sobreviventes não forem revisados. A meta de mutation score elevado permanece **não atendida**
até haver resultado do CI e triagem dos sobreviventes.
