@echo off
REM Script para iniciar el Sistema de Notificaciones
REM Procesa notificaciones de Email y WhatsApp cada 1 minuto
REM Incluye Dashboard web

echo ================================================================================
echo          SISTEMA DE NOTIFICACIONES - Email y WhatsApp
echo ================================================================================
echo.
echo Iniciando sistema...
echo - Procesador de Email (cada 1 minuto)
echo - Procesador de WhatsApp (cada 1 minuto)
echo - Dashboard Web (puerto 8050)
echo.
echo Para detener el sistema, presiona Ctrl+C
echo ================================================================================
echo.

cd /d "%~dp0"

REM Activar entorno virtual si existe
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

REM Ejecutar el sistema
python main.py

pause
