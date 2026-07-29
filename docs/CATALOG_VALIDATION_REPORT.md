# Relatório de validação do catálogo

## Resultado

`INVALID_CATALOG_DATA`

O arquivo `perfis.xlsx` não pode sustentar a expressão
`APROVADO NO ESCOPO COMPUTACIONAL DECLARADO`.

## Identificação

- SHA-256: `EB95CEA376935EF62C8B9C311E0BB8BD72A80EE65BC69811E87CB2C8D2C08001`
- famílias: 4 (`Laminados`, `CS`, `CVS`, `VS`);
- registros: 560;
- manifesto: `catalog/catalog_manifest.yaml`, esquema 1.0;
- fonte oficial, edição, páginas, tolerâncias e revisor: não informados nas quatro famílias.

## Verificações automáticas executadas

- dimensões, propriedades e massa positivas e finitas;
- `d' < d`;
- massa linear comparada a `A · 0,785`;
- `ry²` comparado a `Iy/A`;
- `Wx` comparado a `Ix/(d/2)` para a geometria simétrica declarada;
- `Zx >= Wx`;
- hash do arquivo;
- colunas e unidades obrigatórias;
- duplicidade de designação dentro da família.

As verificações dimensionais acima não substituem a comparação com o catálogo oficial.

## Pendências encontradas

- 4 famílias com `UNVALIDATED_CATALOG_SOURCE`;
- 10 linhas envolvidas em 5 designações duplicadas na família `VS`:
  `300 x 28`, `300 x 31`, `350 x 30`, `350 x 33` e `400 x 32`.

Uma designação repetida pode representar geometrias diferentes. Por isso, a designação sozinha
não é uma chave segura e o software não deve escolher silenciosamente uma das linhas.

## Critério para remoção do bloqueio

Cada família precisa receber fabricante, catálogo, edição, página, origem, hash da fonte, data,
unidades/tolerâncias e revisor. Depois disso, amostras de todas as famílias devem ser comparadas
com a fonte oficial e as duplicidades devem ser resolvidas por identificador inequívoco.

