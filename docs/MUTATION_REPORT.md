# Relatório de testes de mutação

## Estado

`PASS NO ESCOPO DA CAMPANHA CRÍTICA`

O Mutmut 3.6.0 recusa execução nativa no Windows e o ambiente local não possui WSL nem Docker.
A campanha foi executada no GitHub Actions/Linux, run `30478567687`, com o seguinte resultado
observado no log e no artefato:

- mutantes gerados: 124;
- mortos: 124;
- sobreviventes: 0;
- timeout, suspeitos, ignorados ou não verificados: 0;
- mutation score: **100 %** (`124/124`).

O workflow limita a campanha a `src/perfis_metalicos/checks/flexure.py`, usa
`tests/test_flexure_piecewise.py` e publica a lista e o detalhe dos sobreviventes.
O módulo alcançou 100 % de cobertura de statements e branches, mas cobertura não
substitui a capacidade de detectar alterações semânticas.

O resultado atende a meta elevada apenas para a primitiva centralizada de flexão.
Os demais módulos normativos ainda não possuem campanha de mutação equivalente,
portanto não se declara mutation score global do programa.
