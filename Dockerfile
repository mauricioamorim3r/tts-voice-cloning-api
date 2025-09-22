# Dockerfile para TTS Voice Cloning API
FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    espeak \
    espeak-data \
    libespeak1 \
    libespeak-dev \
    festival \
    festvox-kallpc16k \
    && rm -rf /var/lib/apt/lists/*

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements primeiro para cache de layer
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p data/voices outputs logs static

# Expor porta
EXPOSE 8000

# Variáveis de ambiente
ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PORT=8000
ENV DEBUG=False

# Comando de inicialização
CMD ["python", "run_server_real.py", "--host", "0.0.0.0", "--port", "8000"]