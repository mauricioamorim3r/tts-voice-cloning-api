"""
Configurações da aplicação TTS & Voice Cloning
Carrega configurações de variáveis de ambiente
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

# Diretório base do projeto
BASE_DIR = Path(__file__).parent.parent

class Config:
    """Configurações principais da aplicação"""

    # Configurações do servidor
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    HOST: str = os.getenv('HOST', '0.0.0.0')
    PORT: int = int(os.getenv('PORT', 8000))
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')

    # Configurações TTS
    TTS_MODEL_ID: str = os.getenv('TTS_MODEL_ID', 'tts_models/multilingual/multi-dataset/your_tts')
    USE_CUDA: bool = os.getenv('USE_CUDA', 'False').lower() == 'true'
    TTS_CACHE_DIR: str = os.getenv('TTS_CACHE_DIR', str(BASE_DIR / '.cache' / 'tts'))

    # Configurações de áudio
    AUDIO_SAMPLE_RATE: int = int(os.getenv('AUDIO_SAMPLE_RATE', 16000))
    AUDIO_CHANNELS: int = 1  # Mono obrigatório
    MAX_TEXT_LENGTH: int = int(os.getenv('MAX_TEXT_LENGTH', 5000))
    MAX_AUDIO_DURATION: int = int(os.getenv('MAX_AUDIO_DURATION', 300))  # segundos
    MIN_AUDIO_DURATION: int = int(os.getenv('MIN_AUDIO_DURATION', 30))   # segundos

    # Diretórios
    VOICES_DIR: Path = BASE_DIR / os.getenv('VOICES_DIR', 'data/voices')
    OUTPUT_DIR: Path = BASE_DIR / os.getenv('OUTPUT_DIR', 'outputs')
    STATIC_DIR: Path = BASE_DIR / os.getenv('STATIC_DIR', 'static')
    LOGS_DIR: Path = BASE_DIR / os.getenv('LOGS_DIR', 'logs')

    # Configurações de API
    API_RATE_LIMIT: int = int(os.getenv('API_RATE_LIMIT', 60))
    UPLOAD_MAX_SIZE: int = int(os.getenv('UPLOAD_MAX_SIZE', 50_000_000))  # 50MB

    # Formatos suportados
    SUPPORTED_AUDIO_FORMATS: list = ['wav', 'mp3']
    SUPPORTED_INPUT_FORMATS: list = ['.wav', '.mp3', '.flac']
    DEFAULT_LANGUAGE: str = 'pt-BR'

    # Configurações de segurança
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

    def __init__(self):
        """Inicializa configurações e cria diretórios necessários"""
        self._create_directories()
        self._validate_config()

    def _create_directories(self):
        """Cria diretórios necessários se não existirem"""
        for directory in [self.VOICES_DIR, self.OUTPUT_DIR, self.STATIC_DIR, self.LOGS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

    def _validate_config(self):
        """Valida configurações críticas"""
        if self.USE_CUDA:
            try:
                import torch
                if not torch.cuda.is_available():
                    print("⚠️  CUDA solicitado mas não disponível. Usando CPU.")
                    self.USE_CUDA = False
            except ImportError:
                print("⚠️  PyTorch não encontrado. Usando CPU.")
                self.USE_CUDA = False

# Instância global de configuração
config = Config()

# Configuração de logging
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "json": {
            "format": '{"timestamp": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "json",
            "filename": config.LOGS_DIR / "app.log",
            "mode": "a",
        },
    },
    "root": {
        "level": config.LOG_LEVEL,
        "handlers": ["console", "file"],
    },
}