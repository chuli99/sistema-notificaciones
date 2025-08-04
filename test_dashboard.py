#!/usr/bin/env python3
"""
Script de prueba rápida para verificar que Dash funciona correctamente
"""

import logging
import sys

def test_dash_basic():
    """Prueba básica de Dash"""
    try:
        import dash
        from dash import html, dcc
        print(f"✅ Dash importado correctamente - Versión: {dash.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Error importando Dash: {e}")
        return False

def test_dashboard_import():
    """Prueba importación del dashboard"""
    try:
        from dashboard_plotly import get_app
        print("✅ Dashboard importado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error importando dashboard: {e}")
        return False

def test_database_connection():
    """Prueba conexión a base de datos"""
    try:
        from database_config import db_config
        # Intentar una consulta simple
        result = db_config.execute_query("SELECT 1")
        print("✅ Conexión a base de datos exitosa")
        return True
    except Exception as e:
        print(f"❌ Error de conexión a base de datos: {e}")
        return False

def run_quick_dashboard():
    """Ejecuta el dashboard en modo de prueba"""
    try:
        from dashboard_plotly import get_app
        
        app = get_app()
        print("🚀 Iniciando dashboard de prueba...")
        print("📍 Accede a: http://127.0.0.1:8050")
        print("💡 Presiona Ctrl+C para detener")
        
        app.run(
            debug=True,
            host='127.0.0.1',
            port=8050
        )
    except Exception as e:
        print(f"❌ Error ejecutando dashboard: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🔍 DIAGNÓSTICO DEL SISTEMA DE NOTIFICACIONES")
    print("=" * 50)
    
    # Ejecutar pruebas
    tests = [
        ("Importación de Dash", test_dash_basic),
        ("Importación del Dashboard", test_dashboard_import),
        ("Conexión a Base de Datos", test_database_connection),
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        print(f"\n🧪 Probando: {test_name}")
        if not test_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ TODAS LAS PRUEBAS PASARON")
        print("\n¿Quieres ejecutar el dashboard? (s/n): ", end="")
        response = input().strip().lower()
        if response in ['s', 'si', 'y', 'yes']:
            run_quick_dashboard()
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
        print("Por favor revisa los errores antes de continuar.")
        sys.exit(1)
