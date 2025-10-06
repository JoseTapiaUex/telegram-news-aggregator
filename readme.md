# Telegram News Aggregator

Sistema completo para recopilar, procesar y mostrar contenido desde grupos de Telegram.

## 📁 Estructura del Proyecto

```
telegram-news-aggregator/
├── README.md
├── requirements.txt
├── .env.example
├── config.py
├── src/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── telegram_agent.py
│   │   └── content_processor.py
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── app.py
│   │   └── database.py
│   └── frontend/
│       ├── index.html
│       ├── styles.css
│       └── script.js
└── data/
    └── posts.db (se genera automáticamente)
```

## 🚀 Instalación

### 1. Clonar el repositorio
```bash
git clone <tu-repositorio>
cd telegram-news-aggregator
```

### 2. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

**Nota**: El archivo requirements.txt incluye tanto las dependencias core como las opcionales recomendadas para funcionalidad completa (generación de imágenes, parsing rápido, etc.). Si encuentras errores de compilación en Windows (especialmente con `lxml`), consulta la sección de Troubleshooting más abajo.

### 4. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

## ⚙️ Configuración

### Servidor MCP de Telegram
El proyecto asume que ya tienes configurado y corriendo el servidor `telegram-mcp`. 
Asegúrate de que esté ejecutándose antes de iniciar el agente.

### Variables de Entorno (.env)
- `TELEGRAM_GROUP_NAME`: Nombre del grupo/canal de Telegram a monitorear
- `IMAGE_API_KEY`: API key para generación de imágenes (opcional)
- `IMAGE_API_URL`: URL del servicio de generación de imágenes
- `CHECK_INTERVAL`: Intervalo en segundos para revisar nuevos mensajes (default: 300)
- `DATABASE_PATH`: Ruta a la base de datos SQLite (default: data/posts.db)
- `FLASK_PORT`: Puerto para el servidor Flask (default: 5000)

## 🎯 Uso

### 1. Iniciar el Backend (Flask API)
```bash
python src/backend/app.py
```
El servidor estará disponible en `http://localhost:5000`

### 2. Iniciar el Agente de Telegram
```bash
python src/agent/telegram_agent.py
```
El agente comenzará a monitorear el grupo de Telegram y procesará nuevas URLs.

### 3. Acceder al Frontend
Abre en tu navegador:
```
http://localhost:5000
```

## 📡 API Endpoints

### POST /api/posts
Crear un nuevo post
```json
{
  "title": "Título del post",
  "summary": "Resumen breve del contenido",
  "source_url": "https://ejemplo.com/articulo",
  "image_url": "https://ejemplo.com/imagen.jpg",
  "release_date": "2025-10-05",
  "provider": "Nombre del Proveedor",
  "type": "Artículo de Blog"
}
```

### GET /api/posts
Obtener todos los posts
```json
{
  "posts": [
    {
      "id": 1,
      "title": "...",
      "summary": "...",
      ...
    }
  ]
}
```

### GET /api/posts/<id>
Obtener un post específico por ID

## 🔧 Componentes

### Agente de Telegram (`telegram_agent.py`)
- Conecta con el servidor MCP de Telegram
- Recupera mensajes desde la última ejecución
- Identifica URLs en los mensajes
- Delega el procesamiento de contenido

### Procesador de Contenido (`content_processor.py`)
- Extrae información de URLs (título, resumen, imágenes)
- Genera imágenes cuando no hay disponibles
- Estructura los datos del post

### Backend Flask (`app.py`)
- API REST para gestionar posts
- CORS habilitado para el frontend
- Validación de datos

### Base de Datos (`database.py`)
- SQLite para almacenamiento local
- Gestión de la tabla 'posts'
- Operaciones CRUD

### Frontend
- **index.html**: Estructura de la página
- **styles.css**: Diseño responsive y moderno
- **script.js**: Interacción con el API, renderizado dinámico

## 🛠️ Tecnologías

- **Python 3.8+**
- **Flask**: Framework web
- **SQLite**: Base de datos
- **BeautifulSoup4**: Web scraping
- **Requests**: HTTP client
- **MCP (Model Context Protocol)**: Integración con Telegram

## 📝 Notas Importantes

1. El servidor `telegram-mcp` debe estar corriendo antes de iniciar el agente
2. La base de datos se crea automáticamente en el primer inicio
3. El agente guarda el timestamp de la última ejecución para evitar duplicados
4. El frontend se recarga automáticamente cada 30 segundos

## 🐛 Troubleshooting

### Error: "No se puede conectar al servidor MCP"
- Verifica que telegram-mcp esté corriendo
- Comprueba el PID del proceso

### Error: "No se encuentra el grupo de Telegram"
- Verifica el nombre en .env
- Asegúrate de que el bot tenga acceso al grupo

### Error: "API de imágenes no responde"
- Verifica tu API key
- Comprueba la URL del servicio

### Windows: error building wheels (lxml / Microsoft C++ Build Tools)

- Si al instalar dependencias ves un error similar a:
  ```
  error: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools"
  ```
  significa que pip intentó compilar una dependencia (por ejemplo `lxml`) y no encontró una rueda precompilada para tu versión de Python/Windows.

- Recomendado: ejecuta el script preparado `scripts/setup_windows.ps1` desde PowerShell (como Administrador). El script intentará:
  1. Actualizar pip/setuptools/wheel
  2. Instalar dependencias prefiriendo ruedas binarias
  3. Hacer un fallback con `pip` normal
  4. Si falla, intentar instalar `lxml` mediante `pipwin` (ruedas precompiladas)
  5. Si todo falla, sugerirá instalar Visual C++ Build Tools vía `winget` o descargando el instalador

  Para ejecutarlo:
  ```powershell
  # Abre PowerShell como Administrador
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\legacy\scripts\setup_windows.ps1
  ```

  Si prefieres no ejecutar scripts, sigue las instrucciones descritas en la sección anterior sobre instalar Visual C++ Build Tools o descargar la rueda precompilada para `lxml`.

## 📄 Licencia

MIT License - Siéntete libre de usar y modificar este proyecto.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue primero para discutir cambios mayores.