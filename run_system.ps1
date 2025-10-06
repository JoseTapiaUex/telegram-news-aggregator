# Script para lanzar el Telegram News Aggregator
# Uso: .\run_system.ps1

Write-Host "=== TELEGRAM NEWS AGGREGATOR ===" -ForegroundColor Cyan
Write-Host "Iniciando sistema..." -ForegroundColor Green
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-Not (Test-Path "run.py")) {
    Write-Host "❌ Error: run.py no encontrado. Ejecuta este script desde la raíz del proyecto." -ForegroundColor Red
    exit 1
}

# Verificar que el entorno virtual existe
if (-Not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "❌ Error: Entorno virtual no encontrado. Ejecuta: python -m venv .venv" -ForegroundColor Red
    exit 1
}

# Activar entorno virtual
Write-Host "🔧 Activando entorno virtual..." -ForegroundColor Yellow
& .venv\Scripts\Activate.ps1

# Verificar que las dependencias están instaladas
Write-Host "📦 Verificando dependencias..." -ForegroundColor Yellow
python -c "import flask, requests, bs4" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error: Dependencias no instaladas. Ejecuta: pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Dependencias verificadas" -ForegroundColor Green

# Verificar archivo .env
if (-Not (Test-Path ".env")) {
    Write-Host "⚠️  Advertencia: .env no encontrado. Copiando de .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✏️  Edita el archivo .env con tus configuraciones antes de continuar." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Configuraciones requeridas:" -ForegroundColor Cyan
    Write-Host "  - TG_APP_ID: Tu App ID de Telegram" -ForegroundColor White
    Write-Host "  - TG_API_HASH: Tu API Hash de Telegram" -ForegroundColor White
    Write-Host "  - TG_PHONE: Tu número de teléfono" -ForegroundColor White
    Write-Host "  - TELEGRAM_GROUP_NAME: Nombre del grupo a monitorear" -ForegroundColor White
    Write-Host ""
    $response = Read-Host "¿Has configurado el .env? (y/n)"
    if ($response -ne "y") {
        Write-Host "Configura el .env y vuelve a ejecutar este script." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host ""
Write-Host "🚀 Iniciando Telegram News Aggregator..." -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Cyan

# Ejecutar el sistema
python run.py