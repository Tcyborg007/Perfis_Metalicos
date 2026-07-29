# Política de revisão

Toda alteração em fórmula, coeficiente, limite, aplicabilidade ou referência normativa exige,
no mesmo pull request:

1. cópia controlada identificada no manifesto, sem versionar seu conteúdo protegido;
2. item e página conferidos;
3. matriz de rastreabilidade atualizada;
4. teste de fronteira e teste independente;
5. changelog e versão do motor atualizados;
6. relatório de validação atualizado;
7. revisão de engenheiro habilitado, identificado por nome e registro profissional.

Sem um desses elementos, o estado permanece `NORMATIVE_REVIEW_REQUIRED` ou `NOT_CHECKED`.
Resultados de CI não substituem a revisão de engenharia.

O merge em `main` deve exigir ao menos um revisor de software e, para alteração normativa, um
revisor estrutural independente do autor da implementação.
