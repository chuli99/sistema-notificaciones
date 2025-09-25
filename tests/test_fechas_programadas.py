#!/usr/bin/env python3
"""
Script para probar la funcionalidad de fechas programadas
"""

import logging
from datetime import datetime, timedelta
from database_config import db_config
from app.services.alertas_service import ProcesadorNotificaciones

logger = logging.getLogger(__name__)

def crear_notificacion_programada_prueba():
    """Crea notificaciones de prueba con diferentes fechas programadas"""
    try:
        # Obtener un tipo de notificación válido
        tipos_query = "SELECT TOP 1 IdTipoNotificacion FROM Notificaciones_Tipo"
        tipos = db_config.execute_query(tipos_query)
        
        if not tipos:
            print("❌ No hay tipos de notificación configurados")
            return False
        
        tipo_id = tipos[0]['IdTipoNotificacion']
        
        # Crear diferentes tipos de notificaciones programadas
        notificaciones_prueba = [
            {
                'asunto': 'Prueba - Envío Inmediato',
                'cuerpo': 'Esta notificación debe enviarse inmediatamente',
                'fecha_programada': None,
                'descripcion': 'Sin fecha programada'
            },
            {
                'asunto': 'Prueba - Envío Hoy',
                'cuerpo': 'Esta notificación está programada para hoy',
                'fecha_programada': datetime.now(),
                'descripcion': 'Programada para hoy'
            },
            {
                'asunto': 'Prueba - Envío Mañana',
                'cuerpo': 'Esta notificación está programada para mañana',
                'fecha_programada': datetime.now() + timedelta(days=1),
                'descripcion': 'Programada para mañana'
            },
            {
                'asunto': 'Prueba - Envío en 7 días',
                'cuerpo': 'Esta notificación está programada para la próxima semana',
                'fecha_programada': datetime.now() + timedelta(days=7),
                'descripcion': 'Programada para 7 días'
            }
        ]
        
        query = """
        INSERT INTO Notificaciones (IdTipoNotificacion, Asunto, Cuerpo, Estado, Fecha_Programada)
        VALUES (?, ?, ?, 'pendiente', ?)
        """
        
        for notif in notificaciones_prueba:
            params = [
                tipo_id,
                notif['asunto'],
                notif['cuerpo'],
                notif['fecha_programada']
            ]
            
            db_config.execute_non_query(query, params)
            print(f"✅ Creada: {notif['descripcion']} - {notif['asunto']}")
        
        print(f"\n✅ Se crearon {len(notificaciones_prueba)} notificaciones de prueba")
        return True
        
    except Exception as e:
        print(f"❌ Error creando notificaciones de prueba: {e}")
        return False

def probar_procesamiento_fechas():
    """Prueba el procesamiento de notificaciones con fechas programadas"""
    try:
        print("🔍 Probando procesamiento de notificaciones programadas...")
        
        # Verificar qué notificaciones están disponibles para procesar
        query_disponibles = """
        SELECT IdNotificacion, Asunto, Fecha_Programada, Estado
        FROM Notificaciones 
        WHERE Estado = 'pendiente'
          AND (Fecha_Programada IS NULL OR Fecha_Programada <= GETDATE())
        ORDER BY Fecha_Programada ASC
        """
        
        disponibles = db_config.execute_query(query_disponibles)
        print(f"📋 Notificaciones disponibles para procesar: {len(disponibles)}")
        
        for notif in disponibles:
            fecha_info = ""
            if notif['Fecha_Programada']:
                fecha_info = f" (programada: {notif['Fecha_Programada']})"
            else:
                fecha_info = " (inmediata)"
            
            print(f"   - ID {notif['IdNotificacion']}: {notif['Asunto']}{fecha_info}")
        
        # Verificar notificaciones futuras (no se procesarán aún)
        query_futuras = """
        SELECT IdNotificacion, Asunto, Fecha_Programada, Estado
        FROM Notificaciones 
        WHERE Estado = 'pendiente'
          AND Fecha_Programada > GETDATE()
        ORDER BY Fecha_Programada ASC
        """
        
        futuras = db_config.execute_query(query_futuras)
        print(f"⏰ Notificaciones programadas para el futuro: {len(futuras)}")
        
        for notif in futuras:
            print(f"   - ID {notif['IdNotificacion']}: {notif['Asunto']} (programada: {notif['Fecha_Programada']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando procesamiento: {e}")
        return False

def ejecutar_procesador_prueba():
    """Ejecuta el procesador de notificaciones para ver qué se procesa"""
    try:
        print("\n🚀 Ejecutando procesador de notificaciones...")
        ProcesadorNotificaciones.procesar_pendientes()
        print("✅ Procesamiento completado")
        return True
    except Exception as e:
        print(f"❌ Error en procesamiento: {e}")
        return False

def limpiar_notificaciones_prueba():
    """Limpia las notificaciones de prueba creadas"""
    try:
        query = """
        DELETE FROM Notificaciones 
        WHERE Asunto LIKE 'Prueba -%'
        """
        
        db_config.execute_non_query(query, [])
        print("🧹 Notificaciones de prueba eliminadas")
        return True
    except Exception as e:
        print(f"❌ Error limpiando notificaciones: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 PRUEBAS DE FECHAS PROGRAMADAS")
    print("=" * 50)
    
    print("\n1. ¿Crear notificaciones de prueba? (s/n): ", end="")
    if input().strip().lower() in ['s', 'si', 'y', 'yes']:
        crear_notificacion_programada_prueba()
    
    print("\n2. Analizar notificaciones disponibles...")
    probar_procesamiento_fechas()
    
    print("\n3. ¿Ejecutar procesador de notificaciones? (s/n): ", end="")
    if input().strip().lower() in ['s', 'si', 'y', 'yes']:
        ejecutar_procesador_prueba()
    
    print("\n4. ¿Limpiar notificaciones de prueba? (s/n): ", end="")
    if input().strip().lower() in ['s', 'si', 'y', 'yes']:
        limpiar_notificaciones_prueba()
    
    print("\n✅ Pruebas completadas")
