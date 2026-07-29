# Base normativa controlada

## Estado desta base

**NORMATIVE_REVIEW_REQUIRED**

Este documento registra quais fontes estavam realmente disponíveis em 2026-07-29. Ele não
substitui as normas e não declara conformidade. Nenhuma fórmula proveniente de fonte ausente pode
ser incluída, corrigida ou atualizada por inferência.

## Cópia integral disponível

### ABNT NBR 8800:2024

| Campo | Evidência |
|---|---|
| edição observada na capa | terceira edição |
| data observada na capa | 02.10.2024 |
| páginas do arquivo | 293 |
| páginas numeradas declaradas | 276 |
| formato | PDF A4, não criptografado |
| SHA-256 | `8708DF99B709C996745C2D3AE3735063241CBFD3F89594DBB92FE34AA0C8D736` |
| origem | cópia fornecida pelo usuário |
| armazenamento no Git | proibido; somente o hash e os metadados são versionados |

A capa foi renderizada e inspecionada visualmente. O texto foi extraído apenas para localização e
pesquisa; qualquer equação, tabela ou condição deverá ser confirmada também visualmente na página
correspondente, pois extração textual não preserva fielmente notação e diagramação.

O arquivo consultado não contém ocorrência textual identificável de “Errata”, “Er1” ou “2025”.
Portanto, ele é tratado como a edição original de 2024, sem incorporação comprovada da Errata
1:2025.

## Fontes obrigatórias ainda indisponíveis

| Documento requerido | Cópia integral | Consequência |
|---|---|---|
| ABNT NBR 8800:2024/Er1:2025 | não fornecida | `NORMATIVE_REVIEW_REQUIRED`; nenhuma correção atribuída à errata pode ser aceita sem confronto |
| ABNT NBR 8681:2025 | não fornecida | gerador de combinações novo não pode receber coeficientes presumidos |
| ABNT NBR 6120:2019, versão corrigida e errata aplicável | não fornecida | categorias e valores de ações não podem ser codificados como normativos |
| ABNT NBR 6123:2023, versão corrigida e Errata 1:2025 | não fornecida | vento permanece fora do escopo computacional |

## Relações identificadas na cópia da NBR 8800:2024

A cópia de 2024:

- referencia a NBR 8681 como base de critérios de segurança e classificação de ações;
- referencia a NBR 6120 para pesos e ações de uso/ocupação;
- referencia a NBR 6123 para vento;
- contém, em uma nota de tabela, referência explícita à NBR 8681:2003.

Essa última constatação torna obrigatória uma decisão controlada sobre compatibilidade com a
NBR 8681:2025. Até que a edição 2025 seja fornecida e revisada, a aplicação não pode afirmar que
suas combinações representam simultaneamente as duas bases.

## Regra de mudança normativa

Qualquer alteração em função classificada como normativa deve incluir no mesmo conjunto:

1. item e edição confirmados na cópia controlada;
2. evidência visual da página consultada fora do Git;
3. atualização de `norms/normative_manifest.yaml`;
4. atualização da matriz de rastreabilidade;
5. teste independente e teste de fronteira aplicável;
6. changelog e versão do motor;
7. nome, data e decisão do engenheiro revisor.

Sem esses itens, a mudança permanece bloqueada como `NORMATIVE_REVIEW_REQUIRED`.
