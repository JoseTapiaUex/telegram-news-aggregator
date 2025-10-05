"""
Agente principal para monitorear y procesar mensajes de Telegram
Ruta: src/agent/telegram_agent.py
"""
import re
import time
import json
import requests
from datetime import datetime
from pathlib import Path
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config import TELEGRAM_CONFIG, DATABASE_CONFIG
from src.agent.content_processor import ContentProcessor
from src.backend.database import Database


class TelegramAgent:
    """Agente para monitorear grupos de Telegram y procesar URLs"""
    
    def __init__(self):
        self.group_name = TELEGRAM_CONFIG['group_name']
        self.check_interval = TELEGRAM_CONFIG['check_interval']
        self.last_check_file = Path(TELEGRAM_CONFIG['last_check_file'])
        self.content_processor = ContentProcessor()
        self.db = Database()
        self.backend_url = "http://localhost:5000/api/posts"
        
        # Expresión regular para detectar URLs
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
    
    def get_last_check_timestamp(self):
        """Obtiene el timestamp de la última verificación"""
        if self.last_check_file.exists():
            with open(self.last_check_file, 'r') as f:
                return f.read().strip()
        return None
    
    def save_last_check_timestamp(self, timestamp):
        """Guarda el timestamp de la verificación actual"""
        self.last_check_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.last_check_file, 'w') as f:
            f.write(timestamp)
    
    def extract_urls(self, text):
        """Extrae todas las URLs de un texto"""
        if not text:
            return []
        return self.url_pattern.findall(text)
    
    def get_telegram_messages(self):
        """Obtiene mensajes del grupo de Telegram usando las herramientas MCP"""
        print(f"[INFO] Obteniendo mensajes del grupo: {self.group_name}")
        
        try:
            from src.agent.mcp_client import MCPClient
            mcp = MCPClient()
            
            # Obtener mensajes del diálogo
            messages = mcp.get_dialog_messages(dialog_id=self.group_name, limit=50)

            if not messages:
                print(f"[INFO] No se recibieron mensajes (respuesta vacía)")
                return []

            # Si la librería devolvía una lista de dicts (messages ya parseados), OK
            if isinstance(messages, list):
                print(f"[INFO] Obtenidos {len(messages)} mensajes (lista)")
                print(f"[DEBUG] Primer mensaje: {messages[0] if messages else 'None'}")
                return messages

            # Si por alguna razón viene un dict (compatibilidad), intentar extraer
            if isinstance(messages, dict):
                print("[DEBUG] Respuesta tipo dict recibida, intentando extraer 'messages'...")
                # Buscar contenido de mensajes en keys conocidas
                if 'messages' in messages:
                    return messages['messages']
                # Fallback: buscar 'content' -> text JSON
                content = messages.get('content')
                if content and isinstance(content, list):
                    for item in content:
                        if item.get('type') == 'text' and item.get('text'):
                            try:
                                parsed = json.loads(item.get('text'))
                                if isinstance(parsed, dict) and 'messages' in parsed:
                                    return parsed['messages']
                            except Exception:
                                continue
                return []
            
        except Exception as e:
            print(f"[ERROR] Error obteniendo mensajes: {str(e)}")
            return []
    
    def process_message(self, message):
        """Procesa un mensaje individual buscando URLs"""
        # Si el mensaje es un string, extraer URLs directamente del texto
        if isinstance(message, str):
            text = message
            urls = self.extract_urls(text)
            
            if not urls:
                return
            
            print(f"[INFO] Encontradas {len(urls)} URL(s) en mensaje de texto")
            
            for url in urls:
                try:
                    print(f"[INFO] Procesando URL: {url}")
                    post_data = self.content_processor.process_url(url, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    
                    if post_data:
                        self.save_post(post_data)
                        print(f"[SUCCESS] Post guardado: {post_data['title']}")
                    else:
                        print(f"[WARNING] No se pudo procesar la URL: {url}")
                        
                except Exception as e:
                    print(f"[ERROR] Error procesando URL {url}: {str(e)}")
            return
        
        # Si es un diccionario, procesar normalmente
        text = message.get('text', '')
        urls = self.extract_urls(text)
        
        if not urls:
            return
        
        print(f"[INFO] Encontradas {len(urls)} URL(s) en mensaje {message.get('id', 'N/A')}")
        print(f"[DEBUG] Mensaje completo: {message}")
        
        # Fecha del mensaje de Telegram (string 'YYYY-MM-DD HH:MM:SS' esperado)
        message_timestamp = message.get('when')
        print(f"[DEBUG] message_timestamp (when): {message_timestamp}")
        if message_timestamp:
            try:
                message_dt = datetime.strptime(message_timestamp, '%Y-%m-%d %H:%M:%S')
                message_date = message_dt.strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError) as e:
                print(f"[WARNING] Error convirtiendo timestamp {message_timestamp}: {e}")
                message_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            print(f"[WARNING] No se encontró 'when' en el mensaje")
            message_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for url in urls:
            try:
                print(f"[INFO] Procesando URL: {url}")
                post_data = self.content_processor.process_url(url, message_date)
                
                if post_data:
                    self.save_post(post_data)
                    print(f"[SUCCESS] Post guardado: {post_data['title']}")
                else:
                    print(f"[WARNING] No se pudo procesar la URL: {url}")
                    
            except Exception as e:
                print(f"[ERROR] Error procesando URL {url}: {str(e)}")
    
    def save_post(self, post_data):
        """Guarda un post en la base de datos a través del API"""
        try:
            response = requests.post(
                self.backend_url,
                json=post_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 201:
                return response.json()
            else:
                print(f"[ERROR] Error guardando post: {response.status_code}")
                print(f"[ERROR] Response: {response.text}")
                return None
                
        except requests.exceptions.ConnectionError:
            print("[ERROR] No se pudo conectar al backend. ¿Está corriendo?")
            # Fallback: guardar directamente en la base de datos
            return self.db.insert_post(post_data)
        except Exception as e:
            print(f"[ERROR] Error en save_post: {str(e)}")
            return None
    
    def run_once(self):
        """Ejecuta una verificación única del grupo"""
        print(f"\n[INFO] Iniciando verificación - {datetime.now()}")
        
        # Obtener timestamp de la última verificación
        last_check = self.get_last_check_timestamp()
        last_check_dt = None
        if last_check:
            try:
                last_check_dt = datetime.fromisoformat(last_check)
                print(f"[INFO] Última verificación: {last_check_dt}")
            except Exception as e:
                print(f"[WARNING] Error parseando timestamp: {e}")
                last_check_dt = None
        
        # Obtener mensajes de Telegram
        messages = self.get_telegram_messages()
        
        if not messages:
            print("[INFO] No hay mensajes nuevos")
            return
        
        print(f"[INFO] Procesando {len(messages)} mensajes")
        
        # Procesar cada mensaje
        processed_count = 0
        for message in messages:
            if self.should_process_message(message, last_check_dt):
                self.process_message(message)
                processed_count += 1
        
        print(f"[INFO] Procesados {processed_count} mensajes nuevos")
        
        # Guardar timestamp de esta verificación
        current_timestamp = datetime.now().isoformat()
        self.save_last_check_timestamp(current_timestamp)
        
        print(f"[INFO] Verificación completada")
    
    def should_process_message(self, message, last_check_dt):
        """Determina si un mensaje debe procesarse basado en la fecha"""
        if last_check_dt is None:
            # Si no hay timestamp anterior, procesar todos
            return True
        
        if isinstance(message, str):
            # Para mensajes string, procesar (no hay fecha)
            return True
        
        if isinstance(message, dict):
            message_date = message.get('when')
            if message_date:
                try:
                    # Parsear string 'YYYY-MM-DD HH:MM:SS'
                    message_dt = datetime.strptime(message_date, '%Y-%m-%d %H:%M:%S')
                    return message_dt > last_check_dt
                except Exception as e:
                    print(f"[WARNING] Error parseando fecha del mensaje: {e}")
                    return True  # Procesar si no se puede determinar
        
        return True
    
    def run(self):
        """Ejecuta el agente en modo continuo"""
        print(f"[INFO] Agente de Telegram iniciado")
        print(f"[INFO] Monitoreando grupo: {self.group_name}")
        print(f"[INFO] Intervalo de verificación: {self.check_interval}s")
        print(f"[INFO] Presiona Ctrl+C para detener")
        
        try:
            while True:
                self.run_once()
                print(f"[INFO] Esperando {self.check_interval}s hasta la próxima verificación...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print("\n[INFO] Agente detenido por el usuario")
        except Exception as e:
            print(f"\n[ERROR] Error crítico: {str(e)}")
            raise


def main():
    """Función principal"""
    agent = TelegramAgent()
    agent.run()


if __name__ == "__main__":
    main()