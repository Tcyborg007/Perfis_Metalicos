# Base normativa controlada

## Estado desta base

**NORMATIVE_REVIEW_REQUIRED**

Este documento registra quais fontes estavam realmente disponíveis em 2026-07-29. Ele não
substitui as normas e não declara conformidade. Nenhuma fórmula proveniente de fonte ausente pode
ser incluída, corrigida ou atualizada por inferência.

## Cópias integrais disponíveis

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

### ABNT NBR 8681:2025

| Campo | Evidência |
|---|---|
| edição observada na capa | segunda edição |
| data observada na capa | 24.09.2025 |
| páginas do arquivo | 29 |
| páginas numeradas declaradas | 23 |
| SHA-256 | `0D275BBE0B4408309D395F03A26836384E50A35CDB3AC406C8D1F2769FEC7FAE` |
| inspeção visual realizada | páginas numeradas 12 a 19, Seções 5.1.3 a 5.1.6 e Tabelas 1 a 7 |

As equações de combinações últimas e de serviço e as tabelas de coeficientes foram conferidas
visualmente. A fonte integral agora permite transcrição controlada, mas não resolve sozinha as
divergências com as disposições específicas da NBR 8800:2024.

### ABNT NBR 6120:2019

A cópia é a segunda edição original de 30.09.2019, com 66 páginas de PDF e 60 páginas numeradas,
SHA-256 `A525D9D084BBBD36ED4115C1EAD4ECB1A463165DA2C9D05D8B99A352ADEF2B61`.
Ela não se identifica como versão corrigida e não contém errata incorporada comprovada.

### ABNT NBR 6123:2023

A cópia é a segunda edição original de 20.12.2023, com 107 páginas de PDF e 95 páginas numeradas,
SHA-256 `5C8A936D80F6AEA47DA21694DC636411645B7A2AB2850C861BD1A12C6871D6B1`.
Ela não se identifica como versão corrigida nem como incorporando Errata 1:2025.

### Documento fora do escopo

A pasta também contém a ABNT NBR 6118:2026. Ela não foi adotada como fonte de equações para o
escopo atual de perfis de aço e não altera o manifesto desta aplicação.

## Fontes obrigatórias ainda indisponíveis ou incompletas

| Documento requerido | Cópia integral | Consequência |
|---|---|---|
| ABNT NBR 8800:2024/Er1:2025 | não fornecida | `NORMATIVE_REVIEW_REQUIRED`; nenhuma correção atribuída à errata pode ser aceita sem confronto |
| ABNT NBR 6120:2019, versão corrigida e errata aplicável | somente edição original | valores afetados por correção não podem ser promovidos a revisados |
| ABNT NBR 6123:2023, versão corrigida e Errata 1:2025 | somente edição original | vento permanece fora do escopo computacional |

## Relações identificadas na cópia da NBR 8800:2024

A cópia de 2024:

- referencia a NBR 8681 como base de critérios de segurança e classificação de ações;
- referencia a NBR 6120 para pesos e ações de uso/ocupação;
- referencia a NBR 6123 para vento;
- contém, em uma nota de tabela, referência explícita à NBR 8681:2003.

O confronto visual entre as duas edições identificou diferenças em ações permanentes indiretas,
na abrangência de categorias de ocupação e em casos de pontes rolantes. A NBR 8681:2025 declara
que seus coeficientes são indicativos e podem ser alterados ou complementados por normas
específicas. Portanto, a aplicação manterá bases separadas e não selecionará silenciosamente uma
delas até a aprovação da decisão `ND-001`.

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
