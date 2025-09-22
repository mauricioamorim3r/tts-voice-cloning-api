"""
Implementação TTS Real usando pyttsx3 e gTTS
Substitui a dependência Coqui TTS para Windows
"""
import os
import io
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from uuid import uuid4

import pyttsx3
from gtts import gTTS
import soundfile as sf
import librosa
import numpy as np

from .config import config

logger = logging.getLogger(__name__)

class RealTTSSynthesizer:
    """
    Sintetizador TTS real usando pyttsx3 (offline) e gTTS (online)
    """
    
    def __init__(self):
        self.pyttsx3_engine = None
        self.available_voices = {}
        self.current_voice = "default"
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Inicializa os engines TTS"""
        try:
            # Inicializar pyttsx3 (offline)
            self.pyttsx3_engine = pyttsx3.init()
            
            # Configurar propriedades básicas
            self.pyttsx3_engine.setProperty('rate', 150)  # Velocidade
            self.pyttsx3_engine.setProperty('volume', 0.9)  # Volume
            
            # Listar vozes disponíveis
            voices = self.pyttsx3_engine.getProperty('voices')
            
            self.available_voices = {
                "default": {"id": "default", "name": "Voz Padrão", "engine": "pyttsx3", "lang": "pt-BR"},
                "gtts_pt": {"id": "gtts_pt", "name": "Google TTS Português", "engine": "gtts", "lang": "pt"},
                "gtts_en": {"id": "gtts_en", "name": "Google TTS English", "engine": "gtts", "lang": "en"}
            }
            
            # Adicionar vozes do sistema
            for i, voice in enumerate(voices or []):
                voice_id = f"system_{i}"
                self.available_voices[voice_id] = {
                    "id": voice_id,
                    "name": voice.name if hasattr(voice, 'name') else f"Voz Sistema {i}",
                    "engine": "pyttsx3",
                    "lang": "pt-BR",
                    "system_voice": voice
                }
            
            logger.info(f"TTS Real inicializado com {len(self.available_voices)} vozes")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar TTS: {e}")
            self.available_voices = {
                "gtts_pt": {"id": "gtts_pt", "name": "Google TTS Português", "engine": "gtts", "lang": "pt"}
            }
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Retorna lista de vozes disponíveis"""
        return list(self.available_voices.values())
    
    def set_voice(self, voice_id: str) -> bool:
        """Define a voz a ser usada"""
        if voice_id in self.available_voices:
            self.current_voice = voice_id
            
            # Se for voz do sistema, configurar no pyttsx3
            voice_info = self.available_voices[voice_id]
            if voice_info["engine"] == "pyttsx3" and "system_voice" in voice_info:
                try:
                    self.pyttsx3_engine.setProperty('voice', voice_info["system_voice"].id)
                except:
                    pass
            
            return True
        return False
    
    def synthesize_text(
        self,
        text: str,
        voice_id: Optional[str] = None,
        output_path: Optional[str] = None,
        sample_rate: int = 22050
    ) -> str:
        """
        Sintetiza texto em áudio
        
        Args:
            text: Texto para sintetizar
            voice_id: ID da voz (opcional)
            output_path: Caminho do arquivo de saída (opcional)
            sample_rate: Taxa de amostragem
            
        Returns:
            Caminho do arquivo de áudio gerado
        """
        if not text.strip():
            raise ValueError("Texto não pode estar vazio")
        
        # Usar voz especificada ou atual
        voice_to_use = voice_id or self.current_voice
        if voice_to_use not in self.available_voices:
            voice_to_use = "gtts_pt"  # Fallback
        
        voice_info = self.available_voices[voice_to_use]
        
        # Gerar nome único para o arquivo se não especificado
        if not output_path:
            timestamp = int(time.time())
            random_id = str(uuid4())[:8]
            filename = f"tts_{timestamp}_{random_id}.wav"
            output_path = str(config.OUTPUT_DIR / filename)
        
        # Garantir que o diretório existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            if voice_info["engine"] == "gtts":
                return self._synthesize_gtts(text, voice_info, output_path, sample_rate)
            else:
                return self._synthesize_pyttsx3(text, voice_info, output_path, sample_rate)
                
        except Exception as e:
            logger.error(f"Erro na síntese TTS: {e}")
            raise
    
    def _synthesize_gtts(self, text: str, voice_info: Dict, output_path: str, sample_rate: int) -> str:
        """Sintetiza usando Google TTS"""
        try:
            # Criar objeto gTTS
            tts = gTTS(text=text, lang=voice_info["lang"], slow=False)
            
            # Salvar em buffer temporário
            temp_buffer = io.BytesIO()
            tts.write_to_fp(temp_buffer)
            temp_buffer.seek(0)
            
            # Carregar e processar o áudio
            audio_data, original_sr = librosa.load(temp_buffer, sr=None)
            
            # Resample se necessário
            if original_sr != sample_rate:
                audio_data = librosa.resample(audio_data, orig_sr=original_sr, target_sr=sample_rate)
            
            # Salvar arquivo final
            sf.write(output_path, audio_data, sample_rate)
            
            logger.info(f"Áudio sintetizado com gTTS: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erro na síntese gTTS: {e}")
            raise
    
    def _synthesize_pyttsx3(self, text: str, voice_info: Dict, output_path: str, sample_rate: int) -> str:
        """Sintetiza usando pyttsx3"""
        try:
            # Configurar voz se especificada
            if "system_voice" in voice_info:
                self.pyttsx3_engine.setProperty('voice', voice_info["system_voice"].id)
            
            # Salvar em arquivo temporário
            temp_path = output_path.replace('.wav', '_temp.wav')
            
            # pyttsx3 save to file
            self.pyttsx3_engine.save_to_file(text, temp_path)
            self.pyttsx3_engine.runAndWait()
            
            # Verificar se o arquivo foi criado
            if not os.path.exists(temp_path):
                raise Exception("pyttsx3 não conseguiu gerar o arquivo")
            
            # Carregar e processar o áudio
            audio_data, original_sr = librosa.load(temp_path, sr=None)
            
            # Resample se necessário
            if original_sr != sample_rate:
                audio_data = librosa.resample(audio_data, orig_sr=original_sr, target_sr=sample_rate)
            
            # Salvar arquivo final
            sf.write(output_path, audio_data, sample_rate)
            
            # Remover arquivo temporário
            try:
                os.remove(temp_path)
            except:
                pass
            
            logger.info(f"Áudio sintetizado com pyttsx3: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Erro na síntese pyttsx3: {e}")
            # Fallback para gTTS
            logger.info("Tentando fallback para gTTS...")
            gtts_voice = {"engine": "gtts", "lang": "pt"}
            return self._synthesize_gtts(text, gtts_voice, output_path, sample_rate)
    
    def preprocess_text(self, text: str, language: str = "pt") -> str:
        """Pré-processa o texto para síntese"""
        # Remover caracteres especiais e normalizar
        import re
        text = re.sub(r'[^\w\s\.,!?;:-]', '', text)
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o modelo TTS"""
        return {
            "name": "Real TTS Synthesizer",
            "version": "1.0.0",
            "engines": ["pyttsx3", "gTTS"],
            "languages": ["pt", "pt-BR", "en"],
            "description": "TTS real usando pyttsx3 e Google TTS",
            "loaded": True,
            "model_id": "real-tts-v1",
            "device": "cpu"
        }
    
    def get_supported_languages(self) -> List[str]:
        """Retorna idiomas suportados"""
        return ["pt", "pt-BR", "en", "es", "fr", "de", "it"]
    
    async def clone_voice(self, text: str, audio_file: str, voice_id: str) -> bool:
        """Simula clonagem de voz (não implementada)"""
        logger.warning("Clonagem de voz não suportada nesta implementação")
        return False


# Instância global do sintetizador
_synthesizer_instance = None

def get_synthesizer() -> RealTTSSynthesizer:
    """Retorna instância singleton do sintetizador"""
    global _synthesizer_instance
    if _synthesizer_instance is None:
        _synthesizer_instance = RealTTSSynthesizer()
    return _synthesizer_instance

# Alias para compatibilidade
TTSSynthesizer = RealTTSSynthesizer