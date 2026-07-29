# Perfis Metálicos

Aplicação Streamlit para análise de perfis de aço e geração de memorial de cálculo.
As verificações implementadas estão em auditoria contra a ABNT NBR 8800:2024.
Documentos normativos não disponíveis no repositório, inclusive erratas, permanecem
marcados como `NORMATIVE_REVIEW_REQUIRED`.

## Executar localmente

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Publicar no Streamlit Community Cloud

1. Acesse o Streamlit Community Cloud e conecte sua conta do GitHub.
2. Selecione o repositório `Tcyborg007/Perfis_Metalicos` e a branch desejada.
3. Informe `app.py` como arquivo principal.
4. Conclua a implantação. O arquivo `perfis.xlsx` deve permanecer na raiz do repositório.

## Validação

```bash
python -m pytest
python scripts/audit_normative_manifest.py
python scripts/validate_catalog.py
python scripts/validate_determinism.py
python scripts/generate_reproducible_record.py --commit <sha-do-commit>
```

Os resultados produzidos pelo programa devem ser conferidos e validados por profissional legalmente habilitado, considerando o sistema estrutural completo, as hipóteses adotadas e as condições reais da obra.
