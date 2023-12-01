# Imagem Base
FROM continuumio/miniconda3:23.3.1-0

# Defina o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copie o arquivo de requisitos primeiro para melhor armazenamento em cache
COPY requirements.txt /app/

# Instala todas as dependencia
RUN pip install --no-cache-dir -r requirements.txt

# Copia o codigo da aplicação para o diretorio
COPY . /app/

# Libera a porta 5000 para receber requisições
EXPOSE 5000

# Comando para executar a aplicação
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]