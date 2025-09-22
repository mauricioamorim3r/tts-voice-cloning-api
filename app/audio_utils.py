"""
Utilitários para processamento de áudio
Funções para normalização, validação e conversão de arquivos de áudio
"""
import logging
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
import numpy as np

try:
    import librosa
    import soundfile as sf
    AUDIO_LIBS_AVAILABLE = True
except ImportError:
    AUDIO_LIBS_AVAILABLE = False
    print("⚠️  librosa ou soundfile não disponível. Funcionalidades de áudio limitadas.")

from .config import config

logger = logging.getLogger(__name__)

class AudioProcessingError(Exception):
    """Exceção para erros de processamento de áudio"""
    pass

def validate_audio_format(file_path: Path) -> bool:
    """
    Valida se o arquivo de áudio está em formato suportado

    Args:
        file_path: Caminho para o arquivo de áudio

    Returns:
        True se válido, False caso contrário
    """
    if not file_path.exists():
        return False

    # Verificar extensão
    if file_path.suffix.lower() not in config.SUPPORTED_INPUT_FORMATS:
        return False

    if not AUDIO_LIBS_AVAILABLE:
        # Validação básica apenas por extensão
        return True

    try:
        # Tentar carregar o arquivo para validar
        with sf.SoundFile(file_path) as audio:
            duration = len(audio) / audio.samplerate

            # Verificar duração mínima e máxima
            if duration < config.MIN_AUDIO_DURATION:
                logger.warning(f"Áudio muito curto: {duration}s (mínimo: {config.MIN_AUDIO_DURATION}s)")
                return False

            if duration > config.MAX_AUDIO_DURATION:
                logger.warning(f"Áudio muito longo: {duration}s (máximo: {config.MAX_AUDIO_DURATION}s)")
                return False

        return True

    except Exception as e:
        logger.error(f"Erro ao validar áudio: {e}")
        return False

def get_audio_info(file_path: Path) -> Dict[str, Any]:
    """
    Extrai informações detalhadas do arquivo de áudio

    Args:
        file_path: Caminho para o arquivo de áudio

    Returns:
        Dicionário com informações do áudio
    """
    info = {
        "file_path": str(file_path),
        "file_size": 0,
        "exists": file_path.exists(),
        "format": file_path.suffix.lower() if file_path.exists() else None,
    }

    if not file_path.exists():
        return info

    # Informações básicas do arquivo
    stat = file_path.stat()
    info["file_size"] = stat.st_size
    info["modified_time"] = stat.st_mtime

    if not AUDIO_LIBS_AVAILABLE:
        return info

    try:
        # Informações detalhadas do áudio
        with sf.SoundFile(file_path) as audio:
            info.update({
                "duration": len(audio) / audio.samplerate,
                "sample_rate": audio.samplerate,
                "channels": audio.channels,
                "frames": len(audio),
                "format_info": audio.format_info,
                "subtype_info": audio.subtype_info,
            })

        # Análise adicional com librosa se disponível
        try:
            y, sr = librosa.load(file_path, sr=None)
            info.update({
                "rms_energy": float(np.sqrt(np.mean(y**2))),
                "zero_crossing_rate": float(np.mean(librosa.feature.zero_crossing_rate(y))),
                "spectral_centroid": float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))),
            })
        except Exception as e:
            logger.debug(f"Análise avançada falhou: {e}")

    except Exception as e:
        logger.error(f"Erro ao extrair informações do áudio: {e}")
        info["error"] = str(e)

    return info

def normalize_audio(
    input_path: Path,
    output_path: Path,
    target_sr: int = None,
    target_channels: int = 1,
    normalize_volume: bool = True
) -> bool:
    """
    Normaliza arquivo de áudio para padrões do sistema

    Args:
        input_path: Arquivo de entrada
        output_path: Arquivo de saída
        target_sr: Taxa de amostragem alvo (padrão: config.AUDIO_SAMPLE_RATE)
        target_channels: Número de canais (padrão: 1 - mono)
        normalize_volume: Se deve normalizar o volume

    Returns:
        True se sucesso, False caso contrário
    """
    if not AUDIO_LIBS_AVAILABLE:
        logger.error("Bibliotecas de áudio não disponíveis para normalização")
        return False

    if target_sr is None:
        target_sr = config.AUDIO_SAMPLE_RATE

    try:
        logger.info(f"Normalizando áudio: {input_path} -> {output_path}")

        # Carregar áudio
        y, sr = librosa.load(input_path, sr=None, mono=False)

        # Converter para mono se necessário
        if target_channels == 1 and y.ndim > 1:
            y = librosa.to_mono(y)
        elif target_channels > 1 and y.ndim == 1:
            # Duplicar canal mono para estéreo
            y = np.stack([y] * target_channels)

        # Reamostragem se necessário
        if sr != target_sr:
            y = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
            sr = target_sr

        # Normalização de volume
        if normalize_volume:
            # Normalizar para -3dB para evitar clipping
            target_rms = 0.7  # Aproximadamente -3dB
            current_rms = np.sqrt(np.mean(y**2))
            if current_rms > 0:
                scaling_factor = target_rms / current_rms
                # Limitar para evitar amplificação excessiva
                scaling_factor = min(scaling_factor, 3.0)
                y = y * scaling_factor

        # Garantir que está no range válido
        y = np.clip(y, -1.0, 1.0)

        # Criar diretório de saída se não existir
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Salvar arquivo normalizado
        sf.write(output_path, y, sr, format='WAV', subtype='PCM_16')

        logger.info(f"Áudio normalizado com sucesso: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Erro na normalização do áudio: {e}")
        return False

def prepare_audio_for_tts(file_path: Path, output_dir: Path) -> Optional[Path]:
    """
    Prepara arquivo de áudio para uso com TTS (normalização completa)

    Args:
        file_path: Arquivo de entrada
        output_dir: Diretório de saída

    Returns:
        Caminho do arquivo processado ou None se erro
    """
    if not validate_audio_format(file_path):
        logger.error(f"Formato de áudio inválido: {file_path}")
        return None

    # Nome do arquivo processado
    output_path = output_dir / f"processed_{file_path.stem}.wav"

    # Normalizar áudio
    if normalize_audio(file_path, output_path):
        return output_path
    else:
        return None