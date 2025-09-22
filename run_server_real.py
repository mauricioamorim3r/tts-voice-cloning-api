#!/usr/bin/env python3
"""
Script de execução para TTS & Voice Cloning API
Configurado para desenvolvimento no VS Code
"""
import argparse
import sys
import os
import logging
from pathlib import Path

# Adicionar diretório raiz ao Python path
sys.path.insert(0, str(Path(__file__).parent))

def check_dependencies():
    """Verifica se todas as dependências estão instaladas"""
    try:
        # Dependências básicas que precisamos
        import fastapi
        import uvicorn
        import soundfile
        import librosa
        import pyttsx3
        import gtts
        
        print("✅ Dependências verificadas")
        
        # Verificar se pyttsx3 funciona
        try:
            engine = pyttsx3.init()
            print("🎤 pyttsx3 funcionando")
        except:
            print("⚠️  pyttsx3 com problemas, usando apenas gTTS")
        
        return True
        
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("Execute: pip install fastapi uvicorn soundfile librosa pyttsx3 gtts")
        return False

def setup_directories():
    """Cria diretórios necessários"""
    directories = [
        "data/voices",
        "outputs", 
        "logs",
        "static",
        ".cache/tts"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("📁 Diretórios configurados")

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="TTS & Voice Cloning Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Host do servidor"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Porta do servidor"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Auto-reload para desenvolvimento"
    )
    parser.add_argument(
        "--log-level", 
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Nível de log"
    )
    parser.add_argument(
        "--workers", 
        type=int, 
        default=1,
        help="Número de workers (produção)"
    )
    parser.add_argument(
        "--check-only", 
        action="store_true",
        help="Apenas verificar dependências"
    )
    
    args = parser.parse_args()
    
    # Banner
    print("🎤  TTS & Voice Cloning Server")
    print("=" * 40)
    
    # Verificações iniciais
    if not check_dependencies():
        sys.exit(1)
    
    setup_directories()
    
    if args.check_only:
        print("✅ Todas as verificações passaram!")
        sys.exit(0)
    
    # Configurar variáveis de ambiente
    os.environ['LOG_LEVEL'] = args.log_level.upper()
    
    # Importar e executar aplicação
    try:
        import uvicorn
        from app.main import app
        
        print(f"🚀 Iniciando servidor...")
        print(f"📡 Host: {args.host}:{args.port}")
        print(f"🌐 Interface: http://localhost:{args.port}/static/index.html")
        print(f"📚 API Docs: http://localhost:{args.port}/docs")
        print(f"🔄 Reload: {'Sim' if args.reload else 'Não'}")
        print(f"📊 Log Level: {args.log_level}")
        print("=" * 40)
        
        # Configuração para VS Code debugging
        if args.reload:
            print("🐛 Modo desenvolvimento ativo")
            print("💡 Use F5 no VS Code para debug com breakpoints")
        
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level,
            workers=1 if args.reload else args.workers,
            access_log=True
        )
        
    except ImportError as e:
        print(f"❌ Erro ao importar aplicação: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Servidor finalizado pelo usuário")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()