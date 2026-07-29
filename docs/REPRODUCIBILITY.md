# Registro reproduzível da análise

O arquivo `examples/reproducible_analysis_input.json` é uma entrada canônica e
versionada para o motor genérico de análise elástica. O comando

```bash
python scripts/generate_reproducible_record.py --commit <sha-do-commit>
```

gera `build/reproducible_analysis_record.json` com:

- hash SHA-256 da entrada canônica;
- hash do catálogo de perfis e do manifesto normativo;
- versão do esquema, versão do motor e commit;
- reações, extremos, posições críticas e erro estimado;
- convenção de sinais e escopo declarado;
- pendências que impedem a classificação como aprovada.

O artefato é determinístico para a mesma entrada e ambiente bloqueado. Ele não é,
por si só, um memorial completo nem uma validação normativa. Nesta etapa, o
registro cobre apenas análise elástica linear de viga prismática de um vão. As
combinações normativas de produção, resistências, detalhamento e evidência
independente permanecem explicitamente pendentes.

O pipeline executa a geração em Python 3.11 e 3.13 e publica o JSON junto do
relatório de cobertura. Qualquer mudança na entrada altera seu hash; os hashes das
fontes controladas permitem detectar deriva do catálogo ou do manifesto.
