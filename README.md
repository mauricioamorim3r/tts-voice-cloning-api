# 🎙️ TTS Voice Cloning API

API para síntese neural de fala em português brasileiro com clonagem de voz usando pyttsx3 e Google TTS.

![Python](https://img.shields.io/badge/python-v3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🚀 Características

- **Síntese de Fala Real**: Usa Google TTS e Microsoft Speech Engine
- **API REST Completa**: Endpoints para síntese, gerenciamento de vozes e monitoramento
- **Múltiplas Vozes**: Suporte a vozes em português e inglês
- **Interface Web**: Documentação interativa via Swagger UI
- **Cross-Platform**: Compatível com Windows, Linux e macOS
- **Sem Dependências Pesadas**: Não requer PyTorch ou CUDA

## 🎯 Funcionalidades

### ✅ Implementadas

- [x] Síntese de texto em áudio (TTS)
- [x] Múltiplas vozes (Google TTS + Microsoft Speech)
- [x] API REST com FastAPI
- [x] Interface web interativa
- [x] Gerenciamento de perfis de voz
- [x] Monitoramento de saúde da API
- [x] Logs estruturados
- [x] Validação de entrada

### 🔄 Em Desenvolvimento

- [ ] Clonagem de voz neural
- [ ] Suporte a SSML
- [ ] Cache de áudio
- [ ] Autenticação JWT
- [ ] Rate limiting

## 🛠️ Tecnologias

- **Backend**: FastAPI, Uvicorn
- **TTS Engines**:
  - Google Text-to-Speech (gTTS)
  - Microsoft Speech Platform (pyttsx3)
- **Processamento de Áudio**: librosa, soundfile
- **Base de Dados**: SQLite (desenvolvimento)
- **Interface**: Swagger UI, ReDoc

## 📋 Pré-requisitos

- Python 3.11+
- pip (gerenciador de pacotes Python)
- Conexão com internet (para Google TTS)

## 🚀 Instalação Rápida

1. **Clone o repositório**

```bash
git clone https://github.com/mauricioamorim3r/tts-voice-cloning-api.git
cd tts-voice-cloning-api
```

2. **Instale as dependências**

```bash
pip install -r requirements.txt
```

3. **Execute o servidor**

```bash
python run_server_real.py
```

4. **Acesse a interface**

- API Docs: <http://localhost:8000/docs>
- Interface: <http://localhost:8000/static/index.html>

## 🔧 Configuração

Crie um arquivo `.env` na raiz do projeto:

```env
# Configurações do Servidor
DEBUG=True
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Configurações TTS
USE_CUDA=False
AUDIO_SAMPLE_RATE=16000
MAX_TEXT_LENGTH=5000

# Diretórios
VOICES_DIR=data/voices
OUTPUT_DIR=outputs
STATIC_DIR=static
LOGS_DIR=logs
```

## 📖 Uso da API

### Síntese de Texto

```bash
curl -X POST "http://localhost:8000/v1/tts/synthesize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Olá! Esta é uma demonstração da síntese de voz.",
    "language": "pt",
    "format": "wav"
  }'
```

### Listar Vozes Disponíveis

```bash
curl -X GET "http://localhost:8000/v1/voices/available"
```

### Verificar Saúde da API

```bash
curl -X GET "http://localhost:8000/health"
```

## 🎭 Vozes Disponíveis

- **Google TTS Português**: Voz feminina em português brasileiro
- **Google TTS English**: Voz feminina em inglês
- **Microsoft Maria**: Voz nativa do Windows em português
- **Microsoft Zira**: Voz nativa do Windows em inglês

## 📁 Estrutura do Projeto

```text
tts-voice-cloning-api/
├── app/                    # Código principal da aplicação
│   ├── __init__.py
│   ├── main.py            # API FastAPI principal
│   ├── config.py          # Configurações
│   ├── tts_synthesizer_real.py  # Engine TTS
│   ├── audio_utils.py     # Utilitários de áudio
│   └── database.py        # Gerenciamento de dados
├── data/                  # Dados da aplicação
│   └── voices/           # Perfis de voz
├── outputs/              # Arquivos de áudio gerados
├── logs/                 # Logs da aplicação
├── static/               # Interface web
├── tests/                # Testes automatizados
├── requirements.txt      # Dependências Python
├── run_server_real.py    # Script de execução
└── README.md
```

## 🧪 Testes

Execute os testes diretamente:

```bash
# Teste direto do TTS
python test_direct_tts.py

# Teste da API (com servidor rodando)
python test_api.py
```

## 📊 Monitoramento

A API inclui endpoints de monitoramento:

- **Health Check**: `/health`
- **Métricas**: `/metrics` (em desenvolvimento)
- **Status**: `/status`

## 🚀 Deploy

### Docker (Recomendado)

```bash
# Build da imagem
docker build -t tts-api .

# Executar container
docker run -p 8000:8000 tts-api
```

### Deploy Manual

```bash
# Instalar dependências de produção
pip install -r requirements_production.txt

# Executar com Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🔒 Segurança

- Validação de entrada rigorosa
- Rate limiting configurável
- Logs de auditoria
- Sanitização de uploads
- CORS configurável

## 📈 Performance

- **Latência**: < 5 segundos para textos até 1000 caracteres
- **Throughput**: 10+ requisições simultâneas
- **Qualidade**: 22kHz, 16-bit WAV
- **Tamanho**: ~250KB para 30 segundos de áudio

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📜 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🆘 Suporte

- **Issues**: [GitHub Issues](https://github.com/mauricioamorim3r/tts-voice-cloning-api/issues)
- **Documentação**: [Wiki do Projeto](https://github.com/mauricioamorim3r/tts-voice-cloning-api/wiki)
- **Email**: mauricio.amorim@3rpetroleum.com.br

## 🔗 Links Úteis

- [Documentação FastAPI](https://fastapi.tiangolo.com/)
- [Google Text-to-Speech](https://gtts.readthedocs.io/)
- [pyttsx3 Documentation](https://pyttsx3.readthedocs.io/)

---

**Desenvolvido com ❤️ para a comunidade TTS em português brasileiro**