#!/usr/bin/env python3
"""
Main entry point for the Telegram MCP Server.
Handles Telegram MCP server initialization and Python backend startup.
"""

import asyncio
import sys
import logging
import os
import subprocess
import shutil
from pathlib import Path
from dotenv import load_dotenv
import threading
import webbrowser
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "Src"))

from backend.app import create_app
from config import FLASK_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('telegram_mcp.log')
    ]
)

logger = logging.getLogger(__name__)


def setup_telegram_mcp():
    """
    Configura y levanta el servidor Telegram MCP (Node.js) en segundo plano.
    Este servidor maneja la autenticación y comunicación con Telegram.
    """
    logger.info("=" * 60)
    logger.info("Iniciando configuración de Telegram MCP Server (Node.js)")
    logger.info("=" * 60)
    
    # Verificar que npx esté disponible
    npx_path = shutil.which("npx")
    if not npx_path:
        logger.error("'npx' no está disponible. Instala Node.js primero.")
        logger.error("Descarga desde: https://nodejs.org/")
        return False
    
    logger.info(f"npx encontrado en: {npx_path}")
    
    # Cargar variables de entorno desde .env
    load_dotenv()
    
    app_id = os.getenv("TG_APP_ID")
    api_hash = os.getenv("TG_API_HASH")
    phone = os.getenv("TG_PHONE")
    
    # Validar credenciales
    if not all([app_id, api_hash, phone]):
        logger.error("=" * 60)
        logger.error("FALTAN CREDENCIALES DE TELEGRAM EN .env")
        logger.error("=" * 60)
        logger.error("Asegúrate de tener estas variables en tu archivo .env:")
        logger.error("  - TG_APP_ID=tu_app_id")
        logger.error("  - TG_API_HASH=tu_api_hash")
        logger.error("  - TG_PHONE=tu_numero_telefono")
        logger.error("")
        logger.error("Obtén tus credenciales en: https://my.telegram.org/apps")
        return False
    
    logger.info("Credenciales de Telegram cargadas correctamente")
    logger.info(f"  - APP_ID: {app_id}")
    logger.info(f"  - PHONE: {phone}")
    
    try:
        # Paso 1: Autenticación con Telegram MCP
        logger.info("-" * 60)
        logger.info("Paso 1/2: Autenticando con Telegram...")
        logger.info("-" * 60)
        
        auth_command = [
            npx_path, "-y", "@chaindead/telegram-mcp", "auth",
            "--app-id", app_id,
            "--api-hash", api_hash,
            "--phone", phone
        ]
        
        logger.info(f"Ejecutando: {' '.join(auth_command)}")
        
        result = subprocess.run(
            auth_command,
            check=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.stdout:
            logger.info(f"Salida: {result.stdout}")
        
        logger.info("Autenticación completada exitosamente")
        
        # El servidor MCP se inicia por cada llamada del cliente, no necesita background
        logger.info("=" * 60)
        logger.info("Telegram MCP Server configurado correctamente")
        logger.info("=" * 60)
        
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("Timeout durante la autenticación con Telegram")
        logger.error("Esto puede ocurrir si se requiere código de verificación")
        logger.error("Intenta ejecutar manualmente: npx -y @chaindead/telegram-mcp auth")
        return False
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error ejecutando comando de Telegram MCP")
        logger.error(f"Código de salida: {e.returncode}")
        if e.stdout:
            logger.error(f"Salida: {e.stdout}")
        if e.stderr:
            logger.error(f"Error: {e.stderr}")
        return False
        
    except FileNotFoundError as e:
        logger.error(f"No se encontró el comando: {e}")
        logger.error("Verifica que npx esté instalado correctamente")
        return False
        
    except Exception as e:
        logger.error(f"Error inesperado configurando Telegram MCP: {str(e)}")
        logger.exception(e)
        return False


async def main():
    """Main function to run the complete system."""
    try:
        logger.info("")
        logger.info("*" * 60)
        logger.info("*** INICIANDO TELEGRAM NEWS AGGREGATOR SYSTEM ***")
        logger.info("*" * 60)
        logger.info("")
        
        # Paso 1: Configurar y levantar servidor Telegram MCP (Node.js)
        mcp_success = setup_telegram_mcp()
        
        if not mcp_success:
            logger.error("")
            logger.error("!" * 60)
            logger.error("No se pudo iniciar el servidor Telegram MCP")
            logger.error("El sistema puede continuar pero no podrá leer Telegram")
            logger.error("!" * 60)
            logger.error("")
            
            # Preguntar si desea continuar
            response = input("¿Deseas continuar sin conexión a Telegram? (s/n): ")
            if response.lower() != 's':
                logger.info("Sistema detenido por el usuario")
                sys.exit(1)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("Iniciando Backend API REST (Python)")
        logger.info("=" * 60)
        
        # Paso 2: Crear aplicación Flask
        app = create_app()

        # Iniciar Flask thread inmediatamente
        def run_flask():
            app.run(
                host=FLASK_CONFIG['host'],
                port=FLASK_CONFIG['port'],
                debug=FLASK_CONFIG['debug'],
                use_reloader=False
            )
        
        flask_thread = threading.Thread(target=run_flask, daemon=False)
        flask_thread.start()
        
        # Esperar un poco para que Flask inicie
        time.sleep(2)
        
        # Abrir navegador automáticamente
        logger.info("Abriendo navegador web...")
        try:
            # Abrir index.html en el navegador predeterminado
            webbrowser.open(f'http://localhost:{FLASK_CONFIG["port"]}/')
            logger.info("Navegador abierto exitosamente con index.html")
        except Exception as e:
            logger.warning(f"No se pudo abrir el navegador automáticamente: {e}")
        
        # Ejecutar verificación inicial de mensajes
        logger.info("")
        logger.info("=" * 60)
        logger.info("Obteniendo mensajes iniciales de Telegram")
        logger.info("=" * 60)

        from src.agent.telegram_agent import TelegramAgent
        agent = TelegramAgent()
        agent.run_once()
        
        # Iniciar agente de monitoreo continuo
        def run_agent():
            agent.run()
        
        agent_thread = threading.Thread(target=run_agent, daemon=False)
        agent_thread.start()
        
        # Mantener el programa corriendo
        while True:
            await asyncio.sleep(1)
        
    except KeyboardInterrupt:
        logger.info("")
        logger.info("=" * 60)
        logger.info("Recibida señal de interrupción, cerrando servicios...")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error crítico ejecutando el sistema: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Sistema detenido por el usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)
