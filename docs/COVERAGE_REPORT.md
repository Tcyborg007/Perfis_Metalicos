# Relatório de cobertura

## Execução local

- data: 2026-07-29;
- Python: 3.13.5;
- comando: `python -m pytest --cov --cov-branch`;
- testes: 179 aprovados;
- cobertura total do pacote novo: **90,06 %** com branches;
- limite atual de CI: 85 %;
- meta de aceite: 95 % no núcleo e 100 % de branches nas funções normativas críticas.

## Módulos críticos

| Módulo | Cobertura |
|---|---:|
| `analysis.beam_fem` | 95 % |
| `analysis.envelope` | 91 % |
| `analysis.stability_segments` | 87 % |
| `checks.flexure` | 100 % |
| `checks.localized_forces` | 95 % |
| `checks.serviceability` | 90 % |
| `combinations.generator` | 86 % |
| `combinations.nbr8681_2025` | 96 % |
| total do pacote | 90,06 % |

## Conclusão

A meta final de 95 % **não foi atingida**. A medição atual é 90,06 %. O limite de CI em 85 % impede regressão abaixo do
patamar atual, mas não deve ser interpretado como critério final satisfeito. Os ramos ainda não
cobertos permanecem listados no relatório produzido pelo workflow.
