"""
Configuración centralizada del proyecto
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Rutas base del proyecto
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
SRC_DIR = BASE_DIR / 'src'

# Crear directorio de datos si no existe
DATA_DIR.mkdir(exist_ok=True)

# Configuración de Telegram
TELEGRAM_CONFIG = {
    'group_name': os.getenv('TELEGRAM_GROUP_NAME', 'mi_grupo'),
    'check_interval': int(os.getenv('CHECK_INTERVAL', 300)),
    'last_check_file': os.getenv('LAST_CHECK_FILE', str(DATA_DIR / 'last_check.txt'))
}

# Configuración de Base de Datos
DATABASE_CONFIG = {
    'path': os.getenv('DATABASE_PATH', str(DATA_DIR / 'posts.db'))
}

# Configuración del Backend Flask
FLASK_CONFIG = {
    'host': os.getenv('FLASK_HOST', '0.0.0.0'),
    'port': int(os.getenv('FLASK_PORT', 5000)),
    'debug': os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
}

# Configuración de API de Imágenes
IMAGE_API_CONFIG = {
    'api_key': os.getenv('IMAGE_API_KEY', ''),
    'api_url': os.getenv('IMAGE_API_URL', ''),
    'service': os.getenv('IMAGE_SERVICE', 'openai')
}

# Configuración de Web Scraping
SCRAPING_CONFIG = {
    'timeout': int(os.getenv('REQUEST_TIMEOUT', 10)),
    'user_agent': os.getenv('USER_AGENT', 
                            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
}

# Configuración de Tipos de Contenido
CONTENT_TYPES = [
    'Artículo de Blog',
    'Noticia',
    'Video',
    'Investigación',
    'Tutorial',
    'Documentación',
    'Otro'
]