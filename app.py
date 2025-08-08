import streamlit as st

# Garanta que este seja o PRIMEIRO comando do Streamlit no arquivo
st.set_page_config(layout="wide")

st.title("Teste de Layout Largo")
st.write("Se esta página estiver larga, o problema não é o ambiente, mas sim o arquivo principal do aplicativo.")

st.sidebar.header("Barra Lateral de Teste")

col1, col2 = st.columns(2)

with col1:
    st.header("Coluna 1")
    st.info("Esta coluna deveria ocupar metade da área principal.")

with col2:
    st.header("Coluna 2")
    st.info("Esta coluna deveria ocupar a outra metade da área principal.")