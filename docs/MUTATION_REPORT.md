# Relatório de testes de mutação

## Estado

`PARTIAL — SCORE ABAIXO DA META`

O Mutmut 3.6.0 recusa execução nativa no Windows e o ambiente local não possui WSL nem Docker.
A campanha foi executada no GitHub Actions/Linux, run `30478048679`, com o seguinte resultado
observado no log e no artefato:

- mutantes gerados: 124;
- mortos: 92;
- sobreviventes: 32;
- timeout, suspeitos, ignorados ou não verificados: 0;
- mutation score: **74,19 %** (`92/124`).

O workflow limita a campanha a `src/perfis_metalicos/checks/flexure.py`, usa
`tests/test_flexure_piecewise.py` e publica a lista e o detalhe dos sobreviventes.
O módulo alcançou 100 % de cobertura de statements e branches, mas cobertura não
substitui a capacidade de detectar alterações semânticas.

O job permanece experimental (`continue-on-error`) enquanto os 32 sobreviventes
não forem classificados como equivalentes ou eliminados por testes. A meta de
mutation score elevado permanece **não atendida**.
