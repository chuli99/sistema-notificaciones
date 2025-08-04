#!/usr/bin/env python3
"""
Script para probar específicamente los callbacks del dashboard y detectar errores
"""

import logging
import traceback

def test_dashboard_callbacks():
    """Prueba los callbacks del dashboard"""
    try:
        from dashboard_plotly import get_app
        print("✅ Dashboard importado correctamente")
        
        app = get_app()
        print("✅ App de Dash creada correctamente")
        
        # Verificar que los callbacks estén registrados
        if hasattr(app, 'callback_map'):
            num_callbacks = len(app.callback_map)
            print(f"✅ {num_callbacks} callbacks registrados")
        
        return True
    except Exception as e:
        print(f"❌ Error en callbacks del dashboard: {e}")
        print("Traceback completo:")
        traceback.print_exc()
        return False

def test_dashboard_simple():
    """Ejecuta el dashboard en modo de prueba con manejo de errores mejorado"""
    try:
        from dashboard_plotly import get_app
        
        app = get_app()
        print("🚀 Iniciando dashboard de prueba...")
        print("📍 Dashboard disponible en: http://127.0.0.1:8051")
        print("💡 Presiona Ctrl+C para detener")
        print("🔍 Observa la consola para detectar errores de callbacks")
        
        # Configurar logging para mostrar errores de Dash
        logging.getLogger('dash').setLevel(logging.WARNING)
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        
        app.run(
            debug=True,
            host='127.0.0.1',
            port=8051,  # Puerto diferente para evitar conflictos
            dev_tools_hot_reload=False  # Desactivar hot reload que puede causar problemas
        )
    except Exception as e:
        print(f"❌ Error ejecutando dashboard: {e}")
        traceback.print_exc()
        return False

def test_database_queries():
    """Prueba las consultas específicas del dashboard"""
    try:
        from dashboard_plotly import DashboardNotificacionesPlotly
        
        dashboard = DashboardNotificacionesPlotly()
        print("🧪 Probando consultas de base de datos...")
        
        # Probar obtener tipos de notificación
        tipos = dashboard.obtener_tipos_notificacion()
        print(f"✅ Tipos de notificación encontrados: {len(tipos)}")
        for tipo in tipos[:3]:  # Mostrar solo los primeros 3
            print(f"   - ID: {tipo.get('IdTipoNotificacion')}, Desc: {tipo.get('descripcion')}")
        
        # Probar obtener datos de período
        datos = dashboard.obtener_datos_por_periodo('1_mes')
        print(f"✅ Datos de período obtenidos: {len(datos.get('resultados', []))} registros")
        
        return True
    except Exception as e:
        print(f"❌ Error en consultas de base de datos: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 DIAGNÓSTICO ESPECÍFICO DE CALLBACKS")
    print("=" * 50)
    
    # Configurar logging para ver más detalles
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    tests = [
        ("Consultas de Base de Datos", test_database_queries),
        ("Callbacks del Dashboard", test_dashboard_callbacks),
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        print(f"\n🧪 Probando: {test_name}")
        if not test_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ TODAS LAS PRUEBAS PASARON")
        print("\n¿Quieres ejecutar el dashboard de prueba? (s/n): ", end="")
        try:
            response = input().strip().lower()
            if response in ['s', 'si', 'y', 'yes']:
                test_dashboard_simple()
        except KeyboardInterrupt:
            print("\n👋 Prueba cancelada por el usuario")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
        print("Revisa los errores mostrados arriba.")
