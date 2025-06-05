# Script para instalar dependencias del sistema de notificaciones en Windows
Write-Host "=== Instalando entorno virtual para el sistema de notificaciones ===" -ForegroundColor Green

# Crear entorno virtual si no existe
if (-not (Test-Path -Path ".\.venv")) {
    Write-Host "Creando entorno virtual..." -ForegroundColor Cyan
    python -m venv .venv
} else {
    Write-Host "Entorno virtual ya existe." -ForegroundColor Cyan
}

# Activar el entorno virtual
Write-Host "Activando entorno virtual..." -ForegroundColor Cyan
try {
    & .\.venv\Scripts\Activate.ps1
} catch {
    Write-Host "ERROR: No se pudo activar el entorno virtual" -ForegroundColor Red
    Write-Host "Es posible que necesites ejecutar: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process" -ForegroundColor Yellow
    exit
}

# Actualizar pip
Write-Host "Actualizando pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

# Instalar dependencias desde requirements.txt
Write-Host "Instalando dependencias desde requirements.txt..." -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host "=== Instalación completada ===" -ForegroundColor Green
Write-Host "Para activar el entorno virtual en el futuro:" -ForegroundColor Cyan
Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
