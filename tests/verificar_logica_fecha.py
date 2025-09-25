#!/usr/bin/env python3
"""
Script para verificar que la nueva lógica de fechas (solo día) funciona correctamente
"""

from datetime import datetime, timedelta
from database_config import db_config
import logging

logger = logging.getLogger(__name__)

def probar_logica_solo_fecha():
    """Prueba la nueva lógica que compara solo fechas (sin hora)"""
    
    print("🧪 PROBANDO NUEVA LÓGICA: SOLO FECHA (IGNORA HORA)")
    print("=" * 60)
    
    # Obtener fecha actual
    hoy = datetime.now()
    ayer = hoy - timedelta(days=1) 
    manana = hoy + timedelta(days=1)
    
    print(f"📅 Fecha actual del servidor: {hoy.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Solo fecha (sin hora): {hoy.strftime('%Y-%m-%d')}")
    
    # Crear notificaciones de prueba con diferentes horas pero mismo día
    print(f"\n🧪 Creando notificaciones de prueba...")
    
    # Limpiar pruebas anteriores
    try:
        db_config.execute_non_query("DELETE FROM Notificaciones WHERE Asunto LIKE 'PRUEBA_FECHA_%'", [])
        print("🧹 Limpieza de pruebas anteriores completada")
    except:
        pass
    
    # Obtener un tipo de notificación válido
    tipos_query = "SELECT TOP 1 IdTipoNotificacion FROM Notificaciones_Tipo"
    tipos = db_config.execute_query(tipos_query)
    
    if not tipos:
        print("❌ No hay tipos de notificación configurados")
        return False
    
    tipo_id = tipos[0]['IdTipoNotificacion']
    
    # Escenarios de prueba
    escenarios = [
        # Ayer - diferentes horas
        {
            'fecha': ayer.replace(hour=8, minute=0, second=0),
            'nombre': 'PRUEBA_FECHA_AYER_08AM',
            'debe_procesar': True,
            'razon': 'Ayer (cualquier hora) debe procesarse'
        },
        {
            'fecha': ayer.replace(hour=23, minute=59, second=59),
            'nombre': 'PRUEBA_FECHA_AYER_23PM',
            'debe_procesar': True,
            'razon': 'Ayer (cualquier hora) debe procesarse'
        },
        # Hoy - diferentes horas
        {
            'fecha': hoy.replace(hour=0, minute=0, second=0),
            'nombre': 'PRUEBA_FECHA_HOY_00AM',
            'debe_procesar': True,
            'razon': 'Hoy a las 00:00 debe procesarse'
        },
        {
            'fecha': hoy.replace(hour=12, minute=0, second=0),
            'nombre': 'PRUEBA_FECHA_HOY_12PM',
            'debe_procesar': True,
            'razon': 'Hoy a las 12:00 debe procesarse'
        },
        {
            'fecha': hoy.replace(hour=23, minute=59, second=59),
            'nombre': 'PRUEBA_FECHA_HOY_23PM',
            'debe_procesar': True,
            'razon': 'Hoy a las 23:59 debe procesarse'
        },
        # Mañana - diferentes horas
        {
            'fecha': manana.replace(hour=0, minute=0, second=0),
            'nombre': 'PRUEBA_FECHA_MANANA_00AM',
            'debe_procesar': False,
            'razon': 'Mañana (cualquier hora) NO debe procesarse'
        },
        {
            'fecha': manana.replace(hour=12, minute=0, second=0),
            'nombre': 'PRUEBA_FECHA_MANANA_12PM',
            'debe_procesar': False,
            'razon': 'Mañana (cualquier hora) NO debe procesarse'
        },
    ]
    
    # Crear las notificaciones de prueba
    for i, escenario in enumerate(escenarios):
        query = """
        INSERT INTO Notificaciones (IdTipoNotificacion, Asunto, Cuerpo, Estado, Fecha_Programada, Destinatario)
        VALUES (?, ?, ?, 'pendiente', ?, 'test@ejemplo.com')
        """
        
        params = [
            tipo_id,
            escenario['nombre'],
            escenario['razon'],
            escenario['fecha']
        ]
        
        db_config.execute_non_query(query, params)
        
        fecha_str = escenario['fecha'].strftime('%Y-%m-%d %H:%M:%S')
        esperado = "✅ SÍ" if escenario['debe_procesar'] else "❌ NO"
        
        print(f"   {i+1}. {escenario['nombre']}")
        print(f"      Fecha/Hora: {fecha_str}")
        print(f"      Esperado: {esperado} debe procesarse")
        print(f"      Razón: {escenario['razon']}")
        print()
    
    print(f"✅ Se crearon {len(escenarios)} notificaciones de prueba")
    
    # Ahora probar la consulta
    print(f"\n🔍 PROBANDO CONSULTA CON NUEVA LÓGICA...")
    
    query_nueva = """
    SELECT 
        Asunto,
        Fecha_Programada,
        Estado,
        CAST(Fecha_Programada AS DATE) as FechaSolo,
        CAST(GETDATE() AS DATE) as HoySolo
    FROM Notificaciones 
    WHERE Asunto LIKE 'PRUEBA_FECHA_%'
      AND (Fecha_Programada IS NULL OR CAST(Fecha_Programada AS DATE) <= CAST(GETDATE() AS DATE))
      AND Estado = 'pendiente'
    ORDER BY Fecha_Programada
    """
    
    resultados_nueva = db_config.execute_query(query_nueva)
    
    print(f"📋 Notificaciones que SÍ procesa la nueva lógica: {len(resultados_nueva)}")
    for resultado in resultados_nueva:
        fecha_str = resultado['Fecha_Programada'].strftime('%Y-%m-%d %H:%M:%S')
        fecha_solo = resultado['FechaSolo'].strftime('%Y-%m-%d')
        print(f"   ✅ {resultado['Asunto']}")
        print(f"      Fecha completa: {fecha_str}")
        print(f"      Solo fecha: {fecha_solo}")
    
    # Comparar con lógica anterior (para mostrar diferencia)
    print(f"\n📊 COMPARACIÓN CON LÓGICA ANTERIOR (fecha+hora)...")
    
    query_anterior = """
    SELECT 
        Asunto,
        Fecha_Programada,
        Estado
    FROM Notificaciones 
    WHERE Asunto LIKE 'PRUEBA_FECHA_%'
      AND (Fecha_Programada IS NULL OR Fecha_Programada <= GETDATE())
      AND Estado = 'pendiente'
    ORDER BY Fecha_Programada
    """
    
    resultados_anterior = db_config.execute_query(query_anterior)
    
    print(f"📋 Notificaciones que procesaría lógica anterior: {len(resultados_anterior)}")
    for resultado in resultados_anterior:
        fecha_str = resultado['Fecha_Programada'].strftime('%Y-%m-%d %H:%M:%S')
        print(f"   ⏰ {resultado['Asunto']} - {fecha_str}")
    
    # Validar resultados
    print(f"\n📈 ANÁLISIS DE RESULTADOS:")
    
    # Contar cuántas deberían procesarse según nuestros escenarios
    esperadas_si = sum(1 for e in escenarios if e['debe_procesar'])
    esperadas_no = sum(1 for e in escenarios if not e['debe_procesar'])
    
    print(f"   📊 Escenarios creados:")
    print(f"      - Que SÍ deberían procesarse: {esperadas_si}")
    print(f"      - Que NO deberían procesarse: {esperadas_no}")
    print(f"      - Total: {len(escenarios)}")
    
    print(f"   📊 Resultado nueva lógica:")
    print(f"      - Procesará: {len(resultados_nueva)} notificaciones")
    
    # Verificar si coincide con lo esperado
    if len(resultados_nueva) == esperadas_si:
        print(f"   ✅ PERFECTO: La nueva lógica procesa exactamente las {esperadas_si} notificaciones esperadas")
        exito = True
    else:
        print(f"   ❌ ERROR: Esperábamos {esperadas_si} pero obtuvo {len(resultados_nueva)}")
        exito = False
    
    print(f"\n🧹 Limpiando notificaciones de prueba...")
    try:
        db_config.execute_non_query("DELETE FROM Notificaciones WHERE Asunto LIKE 'PRUEBA_FECHA_%'", [])
        print("✅ Limpieza completada")
    except Exception as e:
        print(f"⚠️ Error en limpieza: {e}")
    
    return exito

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 VERIFICACIÓN: LÓGICA DE FECHA (SOLO DÍA)")
    print("=" * 60)
    print("Esta prueba verifica que el sistema ahora compare solo fechas,")
    print("ignorando completamente las horas.")
    print()
    
    if probar_logica_solo_fecha():
        print("\n" + "=" * 60)
        print("✅ VERIFICACIÓN EXITOSA")
        print("🎯 La nueva lógica funciona correctamente:")
        print("   • Compara solo fechas (ignora horas)")
        print("   • Procesa notificaciones de HOY y días anteriores")
        print("   • NO procesa notificaciones de días futuros")
        print("   • Independiente de la hora específica")
    else:
        print("\n" + "=" * 60)
        print("❌ VERIFICACIÓN FALLÓ")
        print("Por favor revisa la lógica de consulta SQL")
