# Dockerfile
# Usa a imagem oficial do Python como base.
FROM python:3.9-slim

# Define o diretório de trabalho que será usado dentro do contêiner.
WORKDIR /app

# Copia os arquivos de dependências e de dados primeiro.
# Isso otimiza o cache de build do Docker.
COPY requirements.txt ./
COPY perfis.xlsx ./

# Instala as bibliotecas Python necessárias.
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o resto do seu código para dentro do contêiner.
COPY . .

# Informa ao Docker que o contêiner escuta na porta 8501.
EXPOSE 8501

# O comando que será executado quando o contêiner iniciar.
# Ele roda o Streamlit na porta 8501 e permite acesso externo.
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]