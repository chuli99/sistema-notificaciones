#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad del botón "Resuelto"
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.notification_actions_service import NotificationActionsService
from app.services.email_service import EmailService  
from app.utils.database_config import db_config
from datetime import datetime, timedelta
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_resolved_functionality():
    """Prueba la funcionalidad del botón Resuelto"""
    
    print("🧪 PRUEBA: Funcionalidad Botón RESUELTO")
    print("=" * 50)
    
    try:
        # 1. Crear una notificación de prueba
        print("1. Creando notificación de prueba...")
        
        # Obtener tipo de notificación válido
        tipos_query = "SELECT TOP 1 IdTipoNotificacion FROM Notificaciones_Tipo"
        tipos = db_config.execute_query(tipos_query)
        
        if not tipos:
            print("❌ No hay tipos de notificación configurados")
            return False
        
        tipo_id = tipos[0]['IdTipoNotificacion']
        
        # Crear notificación
        query_create = """
        INSERT INTO Notificaciones (IdTipoNotificacion, Asunto, Cuerpo, Destinatario, Estado, TokenRespuesta, FechaExpiracion)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        token_test = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(days=7)
        
        params = [
            tipo_id,
            'PRUEBA - Notificación para probar botón Resuelto',
            'Esta es una notificación de prueba para el botón Resuelto',
            'test@ejemplo.com',
            'enviado',  # Estado inicial: enviado
            token_test,
            expires_at
        ]
        
        notification_id = db_config.execute_non_query_with_return(query_create, params)
        
        if not notification_id:
            print("❌ Error creando notificación de prueba")
            return False
            
        print(f"✅ Notificación creada - ID: {notification_id}")
        
        # 2. Verificar estado inicial
        print("\n2. Verificando estado inicial...")
        
        query_status = "SELECT IdNotificacion, Estado, TokenRespuesta, FechaExpiracion FROM Notificaciones WHERE IdNotificacion = ?"
        result = db_config.execute_query(query_status, [notification_id])
        
        if result:
            print(f"   Estado actual: {result[0]['Estado']}")
            print(f"   Token: {result[0]['TokenRespuesta'][:10]}...")
            print(f"   Expira: {result[0]['FechaExpiracion']}")
        
        # 3. Probar funcionalidad de marcar como resuelto
        print("\n3. Probando mark_as_resolved()...")
        
        result_action = NotificationActionsService.mark_as_resolved(notification_id, token_test)
        
        print(f"   Resultado: {result_action}")
        
        if result_action['success']:
            print("   ✅ Acción ejecutada exitosamente")
        else:
            print(f"   ❌ Error en acción: {result_action['message']}")
            return False
        
        # 4. Verificar cambio de estado
        print("\n4. Verificando cambio de estado...")
        
        result_after = db_config.execute_query(query_status, [notification_id])
        
        if result_after:
            nuevo_estado = result_after[0]['Estado']
            print(f"   Estado después: {nuevo_estado}")
            
            if nuevo_estado == 'resuelto':
                print("   ✅ Estado cambiado correctamente a 'resuelto'")
            else:
                print(f"   ❌ Estado incorrecto: esperaba 'resuelto', obtuvo '{nuevo_estado}'")
                return False
        
        # 5. Probar con token inválido
        print("\n5. Probando con token inválido...")
        
        token_invalido = str(uuid.uuid4())
        result_invalid = NotificationActionsService.mark_as_resolved(notification_id, token_invalido)
        
        if not result_invalid['success']:
            print("   ✅ Rechazó token inválido correctamente")
        else:
            print("   ❌ ERROR: Aceptó token inválido")
            return False
        
        # 6. Probar doble procesamiento
        print("\n6. Probando doble procesamiento...")
        
        result_double = NotificationActionsService.mark_as_resolved(notification_id, token_test)
        
        if not result_double['success']:
            print("   ✅ Rechazó procesamiento doble correctamente")
        else:
            print("   ❌ ERROR: Permitió doble procesamiento")
        
        # 7. Verificar en auditoría
        print("\n7. Verificando registro en auditoría...")
        
        audit_query = """
        SELECT accion, detalle, fecha_aud 
        FROM Auditoria 
        WHERE detalle LIKE ? 
        ORDER BY fecha_aud DESC
        """
        
        audit_results = db_config.execute_query(audit_query, [f'%{notification_id}%'])
        
        if audit_results:
            for audit in audit_results[:2]:  # Mostrar últimos 2
                print(f"   📝 {audit['accion']}: {audit['detalle']}")
        
        # 8. Limpiar datos de prueba
        print("\n8. Limpiando datos de prueba...")
        
        delete_query = "DELETE FROM Notificaciones WHERE IdNotificacion = ?"
        db_config.execute_non_query(delete_query, [notification_id])
        
        print("   ✅ Notificación de prueba eliminada")
        
        return True
        
    except Exception as e:
        logger.error(f"Error en prueba: {e}")
        print(f"❌ Error durante la prueba: {e}")
        return False

def test_email_buttons():
    """Prueba que el HTML del email contenga los tres botones"""
    
    print("\n🧪 PRUEBA: Botones en Email HTML")
    print("=" * 50)
    
    try:
        email_service = EmailService()
        
        # Simular creación de email con botones
        cuerpo_original = "<html><body><h1>Notificación de Prueba</h1><p>Este es el contenido.</p></body></html>"
        notification_id = 12345
        token = "abc123def456"
        
        # Construir email con botones
        cuerpo_con_botones = email_service.build_email_with_actions(cuerpo_original, notification_id, token)
        
        print("HTML generado:")
        print("-" * 30)
        print(cuerpo_con_botones)
        print("-" * 30)
        
        # Verificar que contenga los 3 botones
        botones_esperados = [
            '/received?token=',
            '/resolved?token=',  # NUEVO BOTÓN
            '/cancel?token='
        ]
        
        botones_encontrados = []
        for boton in botones_esperados:
            if boton in cuerpo_con_botones:
                botones_encontrados.append(boton)
                print(f"✅ Botón encontrado: {boton}")
            else:
                print(f"❌ Botón faltante: {boton}")
        
        if len(botones_encontrados) == 3:
            print("\n✅ Todos los botones están presentes")
            return True
        else:
            print(f"\n❌ Solo se encontraron {len(botones_encontrados)}/3 botones")
            return False
            
    except Exception as e:
        print(f"❌ Error probando botones: {e}")
        return False

if __name__ == "__main__":
    print("🧪 PRUEBAS DEL BOTÓN RESUELTO")
    print("=" * 60)
    
    # Ejecutar pruebas
    prueba1 = test_resolved_functionality()
    prueba2 = test_email_buttons()
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS:")
    print(f"   Funcionalidad Resuelto: {'✅ PASÓ' if prueba1 else '❌ FALLÓ'}")
    print(f"   Botones en Email: {'✅ PASÓ' if prueba2 else '❌ FALLÓ'}")
    
    if prueba1 and prueba2:
        print("\n🎉 TODAS LAS PRUEBAS PASARON")
        print("✅ El botón 'Resuelto' está funcionando correctamente")
    else:
        print("\n⚠️ ALGUNAS PRUEBAS FALLARON")
        print("❌ Revisa los errores arriba")