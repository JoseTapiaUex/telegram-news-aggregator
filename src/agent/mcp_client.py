"""
Cliente MCP para comunicarse con el servidor Telegram MCP
Ruta: src/agent/mcp_client.py
"""
import json
import subprocess
import shutil
import os
import time
import threading
from typing import Dict, List, Any, Optional
from pathlib import Path

class MCPClient:
    """Cliente para comunicarse con el servidor MCP de Telegram"""
    
    def __init__(self):
        self.npx_path = shutil.which("npx")
        if not self.npx_path:
            raise RuntimeError("npx no está disponible. Instala Node.js primero.")
        
        # Cargar variables de entorno
        from dotenv import load_dotenv
        load_dotenv()
        
        self.app_id = os.getenv("TG_APP_ID")
        self.api_hash = os.getenv("TG_API_HASH")
        self.phone = os.getenv("TG_PHONE")
        
        # Conexión persistente
        self.process = None
        self.process_lock = threading.Lock()
        self.request_id = 1
    
    def _start_server(self):
        """Inicia el servidor MCP si no está corriendo"""
        if self.process is None or self.process.poll() is not None:
            try:
                self.process = subprocess.Popen(
                    [self.npx_path, "-y", "@chaindead/telegram-mcp"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                # Dar tiempo al servidor para inicializar
                time.sleep(2)
            except Exception as e:
                raise RuntimeError(f"Error iniciando servidor MCP: {str(e)}")
    
    def _stop_server(self):
        """Detiene el servidor MCP"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                try:
                    self.process.kill()
                except:
                    pass
            self.process = None
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """
        Llama a una herramienta MCP usando conexión persistente
        
        Args:
            tool_name: Nombre de la herramienta (tg_me, tg_dialogs, tg_dialog, etc.)
            arguments: Argumentos para la herramienta
        
        Returns:
            Resultado de la herramienta
        """
        if arguments is None:
            arguments = {}
        
        with self.process_lock:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Iniciar servidor si es necesario
                    self._start_server()
                    
                    # Construir el comando MCP
                    mcp_request = {
                        "jsonrpc": "2.0",
                        "id": self.request_id,
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": arguments
                        }
                    }
                    
                    self.request_id += 1
                    
                    # Enviar el request
                    request_json = json.dumps(mcp_request) + "\n"
                    self.process.stdin.write(request_json)
                    self.process.stdin.flush()
                    
                    # Leer respuesta con timeout
                    response = None
                    start_time = time.time()
                    while time.time() - start_time < 30:  # 30 segundos timeout
                        if self.process.poll() is not None:
                            # Proceso terminó, reiniciar
                            break
                        
                        line = self.process.stdout.readline()
                        if line.strip():
                            try:
                                response = json.loads(line)
                                break
                            except json.JSONDecodeError:
                                continue
                    
                    if response:
                        if 'result' in response:
                            return response['result']
                        elif 'error' in response:
                            raise RuntimeError(f"MCP Error: {response['error']}")
                    
                    # Si llegamos aquí, intentar reiniciar el servidor
                    self._stop_server()
                    if attempt < max_retries - 1:
                        time.sleep(1)  # Esperar antes de reintentar
                    
                except Exception as e:
                    self._stop_server()
                    if attempt == max_retries - 1:
                        raise RuntimeError(f"Error llamando a herramienta MCP después de {max_retries} intentos: {str(e)}")
                    time.sleep(1)
            
            return None
    
    def __del__(self):
        """Destructor para asegurar que el servidor se detenga"""
        self._stop_server()
    
    def get_me(self) -> Dict:
        """Obtiene información de la cuenta actual"""
        print("[INFO] Obteniendo información de la cuenta...")
        return self.call_tool("tg_me")
    
    def get_dialogs(self, unread_only: bool = False) -> List[Dict]:
        """Lista todos los diálogos/chats"""
        print(f"[INFO] Obteniendo diálogos (unread_only={unread_only})...")
        args = {"unreadOnly": unread_only} if unread_only else {}
        result = self.call_tool("tg_dialogs", args)
        return result if result else []
    
    def get_dialog_messages(self, dialog_id: str, limit: int = 100) -> List[Dict]:
        """
        Obtiene mensajes de un diálogo específico
        
        Args:
            dialog_id: ID del diálogo (ej: "chat-123456" o "@username")
            limit: Número máximo de mensajes a obtener
        """
        print(f"[INFO] Obteniendo mensajes del diálogo: {dialog_id} (limit={limit})...")

        # El servidor Go espera HistoryArguments{Name: ...}
        # Intentamos primero con la clave 'dialogId' (formato: cht[...], chn[...] o username)
        args = {"dialogId": dialog_id, "limit": limit}
        result = None

        try:
            result = self.call_tool("tg_dialog", args)
        except Exception as e:
            print(f"[DEBUG] Error llamando tg_dialog con 'dialogId': {e}")

        # Si falla o el servidor responde con isError, intentar fallback con 'name'
        if not result or (isinstance(result, dict) and result.get('isError')):
            try:
                print("[DEBUG] Intentando tg_dialog con clave 'name' como fallback")
                result = self.call_tool("tg_dialog", {"name": dialog_id, "limit": limit})
            except Exception as e:
                print(f"[DEBUG] Error llamando tg_dialog con 'name': {e}")
                return []

        # Parsear la respuesta: muchas respuestas vienen como dict {'content': [{ 'text': '<json>' }, ...]}
        try:
            if isinstance(result, dict) and 'content' in result:
                # Buscar primer elemento de tipo text que contenga JSON con key 'messages'
                for item in result['content']:
                    if item.get('type') == 'text' and item.get('text'):
                        text = item.get('text')
                        try:
                            data = json.loads(text)
                            if isinstance(data, dict) and 'messages' in data:
                                return data['messages']
                        except Exception:
                            # no JSON, puede ser un error en texto
                            continue
                # Si no encontramos JSON con messages, devolver empty list
                return []

            # Si el resultado ya es una lista, devolverla
            if isinstance(result, list):
                return result

            return []
        except Exception as e:
            print(f"[ERROR] Error parseando respuesta de tg_dialog: {e}")
            return []
    
    def send_message(self, dialog_id: str, message: str) -> Dict:
        """Envía un mensaje a un diálogo"""
        print(f"[INFO] Enviando mensaje a {dialog_id}...")
        return self.call_tool("tg_send", {
            "dialogId": dialog_id,
            "message": message
        })
    
    def mark_as_read(self, dialog_id: str) -> Dict:
        """Marca un diálogo como leído"""
        print(f"[INFO] Marcando diálogo como leído: {dialog_id}...")
        return self.call_tool("tg_read", {"dialogId": dialog_id})