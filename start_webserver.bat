@echo off
echo ========================================
echo  Sistema de Notificaciones - Servidor Web
echo ========================================
echo.

echo Iniciando servidor para manejar acciones de email...
echo Botones: Marcar como Recibido / Anular Envio
echo.

echo Verificando dependencias...
python -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Flask no esta instalado
    echo Ejecuta: pip install -r requirements.txt
    pause
    exit /b 1
)

echo Verificando archivo .env...
if not exist ".env" (
    echo [ADVERTENCIA] No existe archivo .env
    echo Copia .env.example a .env y configura las variables
    echo.
)

echo [INFO] Iniciando servidor web...
echo [INFO] URL base: http://localhost:5000
echo [INFO] Presiona Ctrl+C para detener
echo.

python web_server.py

echo.
echo Servidor detenido.
pause