"""
API Principal para TTS & Voice Cloning pt-BR - Versão Completa
Implementa todas as funcionalidades com dados reais
"""
import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from uuid import uuid4

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Depends
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, validator
import uvicorn

# Imports locais
from .config import config, LOGGING_CONFIG
from .tts_synthesizer_real import get_synthesizer, RealTTSSynthesizer, TTSSynthesizer
from .audio_utils import normalize_audio, validate_audio_format, get_audio_info, prepare_audio_for_tts
from .database import DatabaseManager, get_database, VoiceProfileCreate, VoiceProfileResponse

# Configuração de logging
import logging.config
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Inicialização da aplicação FastAPI
app = FastAPI(
    title="TTS & Voice Cloning API",
    description="API para síntese neural de fala em português brasileiro com clonagem de voz",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware de segurança
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*"]  # Ajustar para produção
)

# CORS para desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar arquivos estáticos
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")

# Models para validação
class TTSRequest(BaseModel):
    text: str
    language: str = "pt"
    format: str = "wav"
    voice_id: Optional[str] = None

    @validator('text')
    def validate_text_length(cls, v):
        if len(v) > config.MAX_TEXT_LENGTH:
            raise ValueError(f'Texto muito longo. Máximo: {config.MAX_TEXT_LENGTH} caracteres')
        return v

class TTSCloneRequest(BaseModel):
    text: str
    voice_id: str
    format: str = "wav"

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    tts_model_loaded: bool
    tts_model_id: str
    device: str
    uptime: Optional[str] = None

# Variáveis globais para monitoramento
app_start_time = datetime.utcnow()

@app.on_event("startup")
async def startup_event():
    """Inicialização da aplicação"""
    logger.info("Iniciando TTS & Voice Cloning API...")

    # Inicializar database
    db = await get_database()
    await db.init_async()

    # Verificar se o sintetizador carrega corretamente
    try:
        synthesizer = get_synthesizer()
        logger.info("Sintetizador TTS inicializado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar sintetizador: {e}")

    logger.info("API iniciada e pronta para receber requisições")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Página inicial - redireciona para interface web"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>TTS & Voice Cloning</title>
        <meta http-equiv="refresh" content="0; url=/static/index.html">
    </head>
    <body>
        <p>Redirecionando para a interface...</p>
        <p><a href="/static/index.html">Clique aqui se não for redirecionado automaticamente</a></p>
    </body>
    </html>
    """

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Verificação de saúde do sistema"""
    try:
        synthesizer = get_synthesizer()
        model_info = synthesizer.get_model_info()

        uptime = datetime.utcnow() - app_start_time
        uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m"

        return HealthResponse(
            status="healthy",
            version="1.0.0",
            timestamp=datetime.utcnow(),
            tts_model_loaded=model_info.get("loaded", False),
            tts_model_id=model_info.get("model_id", "unknown"),
            device=model_info.get("device", "unknown"),
            uptime=uptime_str
        )
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        raise HTTPException(status_code=503, detail="Serviço temporariamente indisponível")

@app.post("/v1/tts")
async def text_to_speech(
    text: str = Form(...),
    language: str = Form("pt"),
    format: str = Form("wav"),
    voice_id: Optional[str] = Form(None),
    synthesizer: TTSSynthesizer = Depends(get_synthesizer)
):
    """
    Converte texto em áudio usando TTS

    Args:
        text: Texto para sintetizar
        language: Idioma do texto (padrão: pt)
        format: Formato de saída (wav, mp3)
        voice_id: ID do perfil de voz para clonagem (opcional)

    Returns:
        Arquivo de áudio gerado
    """
    start_time = time.time()

    try:
        # Validar entrada
        if len(text) > config.MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Texto muito longo. Máximo: {config.MAX_TEXT_LENGTH} caracteres"
            )

        if format not in config.SUPPORTED_AUDIO_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Formato não suportado. Use: {', '.join(config.SUPPORTED_AUDIO_FORMATS)}"
            )

        # Preparar texto
        processed_text = synthesizer.preprocess_text(text, language)

        # Gerar nome único para o arquivo
        file_id = str(uuid4())
        output_path = config.OUTPUT_DIR / f"tts_{file_id}.{format}"

        # Buscar referência de voz se fornecida
        voice_reference = None
        if voice_id:
            db = await get_database()
            voice_profile = await db.get_voice_profile(voice_id)
            if voice_profile:
                voice_reference = Path(voice_profile['file_path'])
                logger.info(f"Usando perfil de voz: {voice_profile['display_name']}")
            else:
                logger.warning(f"Perfil de voz não encontrado: {voice_id}")

        # Sintetizar áudio
        audio_path = synthesizer.synthesize_text(
            text=processed_text,
            voice_id=voice_id,
            output_path=output_path
        )
        
        success = bool(audio_path and os.path.exists(audio_path))

        if not success or not output_path.exists():
            raise HTTPException(status_code=500, detail="Falha na síntese de áudio")

        processing_time = time.time() - start_time

        # Log estruturado
        logger.info(json.dumps({
            "event": "tts_synthesis",
            "text_length": len(text),
            "language": language,
            "format": format,
            "voice_id": voice_id,
            "processing_time_ms": round(processing_time * 1000, 2),
            "output_file": str(output_path),
            "success": True
        }))

        # Retornar arquivo
        return FileResponse(
            path=output_path,
            media_type=f"audio/{format}",
            filename=f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}",
            headers={
                "X-Processing-Time": str(round(processing_time * 1000, 2)),
                "X-Text-Length": str(len(text)),
                "X-Voice-ID": voice_id or "default"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(json.dumps({
            "event": "tts_synthesis_error",
            "error": str(e),
            "text_length": len(text),
            "processing_time_ms": round(processing_time * 1000, 2),
            "success": False
        }))
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/v1/voices/available")
async def get_available_voices(synthesizer: TTSSynthesizer = Depends(get_synthesizer)):
    """Retorna lista de vozes disponíveis"""
    try:
        voices = synthesizer.get_available_voices()
        return {
            "voices": voices,
            "total": len(voices),
            "supported_languages": synthesizer.get_supported_languages()
        }
    except Exception as e:
        logger.error(f"Erro ao listar vozes: {e}")
        raise HTTPException(status_code=500, detail="Erro ao carregar vozes disponíveis")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower()
    )