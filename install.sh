#!/bin/bash

# Script para instalar dependencias del sistema de notificaciones

echo "=== Instalando entorno virtual para el sistema de notificaciones ==="

# Crear entorno virtual si no existe
if [ ! -d ".venv" ]; then
    echo "Creando entorno virtual..."
    python -m venv .venv
else
    echo "Entorno virtual ya existe."
fi

# Activar el entorno virtual (funciona en Linux/Mac)
source .venv/bin/activate 2>/dev/null || {
    # Si falla, intentar con la activación de Windows
    echo "Intentando activar entorno virtual en Windows..."
    .\.venv\Scripts\activate
}

# Verificar activación
if [ $? -ne 0 ]; then
    echo "ERROR: No se pudo activar el entorno virtual"
    exit 1
fi

# Actualizar pip
echo "Actualizando pip..."
python -m pip install --upgrade pip

# Instalar dependencias desde requirements.txt
echo "Instalando dependencias desde requirements.txt..."
pip install -r requirements.txt

echo "=== Instalación completada ==="
echo "Para activar el entorno virtual:"
echo "  - En Windows: .\.venv\Scripts\activate"
echo "  - En Linux/Mac: source .venv/bin/activate"
