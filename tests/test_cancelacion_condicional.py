"""
Test para verificar que la cancelación en cascada solo afecta 
a notificaciones en estado 'pendiente'
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.utils.database_config import db_config
from app.services.notification_actions_service import NotificationActionsService
import uuid
from datetime import datetime, timedelta

def setup_test_data():
    """
    Crear datos de prueba con notificaciones en diferentes estados
    """
    source_id = str(uuid.uuid4())
    action_token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(days=1)
    
    print("🔧 Configurando datos de prueba...")
    
    # Notificación principal (la que se va a cancelar)
    query_main = """
    INSERT INTO Notificaciones (
        Destinatario, Asunto, Mensaje, Estado, 
        Source_IdNotificacion, action_token, expires_at
    ) 
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    
    main_id = db_config.execute_scalar(
        query_main + "; SELECT SCOPE_IDENTITY()",
        ['test@email.com', 'Notificación Principal', 'Test mensaje', 'enviado', 
         source_id, action_token, expires_at]
    )
    
    # Notificaciones relacionadas en diferentes estados
    test_notifications = [
        ('test1@email.com', 'Relacionada 1', 'pendiente'),
        ('test2@email.com', 'Relacionada 2', 'pendiente'), 
        ('test3@email.com', 'Relacionada 3', 'enviado'),
        ('test4@email.com', 'Relacionada 4', 'recibido'),
        ('test5@email.com', 'Relacionada 5', 'pendiente'),
        ('test6@email.com', 'Relacionada 6', 'procesado')
    ]
    
    related_ids = []
    for email, asunto, estado in test_notifications:
        related_id = db_config.execute_scalar(
            query_main + "; SELECT SCOPE_IDENTITY()",
            [email, asunto, 'Test relacionada', estado, source_id, None, None]
        )
        related_ids.append((related_id, estado))
    
    print(f"✅ Datos de prueba creados:")
    print(f"   - Notificación principal ID: {main_id}")
    print(f"   - Source_IdNotificacion: {source_id}")
    print(f"   - Notificaciones relacionadas: {len(related_ids)}")
    
    return main_id, source_id, action_token, related_ids

def verify_initial_states(source_id):
    """
    Verificar los estados iniciales de las notificaciones
    """
    query = """
    SELECT IdNotificacion, Estado, Asunto
    FROM Notificaciones 
    WHERE Source_IdNotificacion = ?
    ORDER BY IdNotificacion
    """
    
    results = db_config.execute_query(query, [source_id])
    
    print("\n📊 Estados iniciales de las notificaciones:")
    states_count = {}
    for row in results:
        estado = row['Estado']
        states_count[estado] = states_count.get(estado, 0) + 1
        print(f"   - ID {row['IdNotificacion']}: {estado} ({row['Asunto']})")
    
    print(f"\n📈 Resumen inicial:")
    for estado, count in states_count.items():
        print(f"   - {estado}: {count} notificaciones")
    
    return states_count

def test_conditional_cancellation():
    """
    Test principal para verificar la cancelación condicional
    """
    print("🧪 INICIANDO TEST DE CANCELACIÓN CONDICIONAL")
    print("=" * 60)
    
    try:
        # 1. Configurar datos de prueba
        main_id, source_id, action_token, related_ids = setup_test_data()
        
        # 2. Verificar estados iniciales
        initial_states = verify_initial_states(source_id)
        pendiente_inicial = initial_states.get('pendiente', 0)
        
        # 3. Ejecutar cancelación
        print(f"\n🎯 Cancelando notificación principal ID: {main_id}")
        result = NotificationActionsService.cancel_notification(main_id, action_token)
        
        print(f"✅ Resultado de cancelación: {result}")
        
        # 4. Verificar estados finales
        print("\n🔍 Verificando estados después de la cancelación...")
        final_states = verify_final_states(source_id)
        
        # 5. Validar resultados
        validate_results(initial_states, final_states, pendiente_inicial, result)
        
    except Exception as e:
        print(f"❌ Error durante el test: {e}")
        return False
    finally:
        # Limpiar datos de prueba
        cleanup_test_data(source_id)
    
    return True

def verify_final_states(source_id):
    """
    Verificar los estados finales después de la cancelación
    """
    query = """
    SELECT IdNotificacion, Estado, Asunto, cancelled_at
    FROM Notificaciones 
    WHERE Source_IdNotificacion = ?
    ORDER BY IdNotificacion
    """
    
    results = db_config.execute_query(query, [source_id])
    
    print("\n📊 Estados finales de las notificaciones:")
    states_count = {}
    cancelled_count = 0
    
    for row in results:
        estado = row['Estado']
        states_count[estado] = states_count.get(estado, 0) + 1
        cancelled_indicator = "🔥" if row['cancelled_at'] else "  "
        print(f"   {cancelled_indicator} ID {row['IdNotificacion']}: {estado} ({row['Asunto']})")
        
        if row['cancelled_at']:
            cancelled_count += 1
    
    print(f"\n📈 Resumen final:")
    for estado, count in states_count.items():
        print(f"   - {estado}: {count} notificaciones")
    
    print(f"\n🔥 Total de notificaciones con timestamp de cancelación: {cancelled_count}")
    
    return states_count

def validate_results(initial_states, final_states, pendiente_inicial, result):
    """
    Validar que los resultados sean los esperados
    """
    print("\n✅ VALIDACIÓN DE RESULTADOS")
    print("-" * 40)
    
    # Verificar que solo las pendientes cambiaron a cancelado
    pendiente_final = final_states.get('pendiente', 0)
    cancelado_final = final_states.get('cancelado', 0)
    
    # Las notificaciones pendientes deberían haber disminuido
    pendientes_canceladas = pendiente_inicial - pendiente_final
    
    print(f"📊 Notificaciones pendientes iniciales: {pendiente_inicial}")
    print(f"📊 Notificaciones pendientes finales: {pendiente_final}")
    print(f"📊 Notificaciones canceladas total: {cancelado_final}")
    print(f"📊 Pendientes que cambiaron a cancelado: {pendientes_canceladas}")
    
    # Verificar resultado del servicio
    if result and result.get('success'):
        related_cancelled = result.get('related_cancelled', 0)
        total_cancelled = result.get('total_cancelled', 0)
        
        print(f"📊 Según el servicio - Relacionadas canceladas: {related_cancelled}")
        print(f"📊 Según el servicio - Total canceladas: {total_cancelled}")
        
        # Validaciones
        validations = []
        
        # 1. Las pendientes canceladas deben coincidir con las relacionadas canceladas del servicio
        if pendientes_canceladas == related_cancelled:
            validations.append(("✅", f"Pendientes canceladas ({pendientes_canceladas}) coincide con servicio ({related_cancelled})"))
        else:
            validations.append(("❌", f"Pendientes canceladas ({pendientes_canceladas}) NO coincide con servicio ({related_cancelled})"))
        
        # 2. Solo deben haberse cancelado las pendientes + la principal
        expected_total = pendiente_inicial + 1  # +1 por la principal
        if cancelado_final == expected_total:
            validations.append(("✅", f"Total canceladas ({cancelado_final}) es correcto ({expected_total} esperado)"))
        else:
            validations.append(("❌", f"Total canceladas ({cancelado_final}) es incorrecto ({expected_total} esperado)"))
        
        # 3. Verificar que notificaciones en otros estados no cambiaron
        otros_estados = ['enviado', 'recibido', 'procesado']
        otros_mantuvieron = True
        for estado in otros_estados:
            inicial = initial_states.get(estado, 0)
            final = final_states.get(estado, 0)
            if inicial != final:
                otros_mantuvieron = False
                validations.append(("❌", f"Estado '{estado}' cambió de {inicial} a {final}"))
        
        if otros_mantuvieron:
            validations.append(("✅", "Notificaciones en otros estados se mantuvieron sin cambios"))
        
        print(f"\n🎯 RESULTADOS DE VALIDACIÓN:")
        for status, message in validations:
            print(f"   {status} {message}")
        
        # Resultado final
        all_passed = all(status == "✅" for status, _ in validations)
        if all_passed:
            print(f"\n🎉 ¡TODAS LAS VALIDACIONES PASARON!")
            print(f"   La lógica condicional funciona correctamente.")
        else:
            print(f"\n⚠️  ALGUNAS VALIDACIONES FALLARON")
            print(f"   Revisar la implementación.")
        
        return all_passed
    else:
        print(f"❌ El servicio de cancelación falló: {result}")
        return False

def cleanup_test_data(source_id):
    """
    Limpiar los datos de prueba
    """
    try:
        # Eliminar todas las notificaciones de prueba
        query_delete = "DELETE FROM Notificaciones WHERE Source_IdNotificacion = ?"
        deleted = db_config.execute_non_query(query_delete, [source_id])
        print(f"\n🧹 Datos de prueba eliminados: {deleted} registros")
        
    except Exception as e:
        print(f"⚠️ Error limpiando datos de prueba: {e}")

if __name__ == "__main__":
    success = test_conditional_cancellation()
    
    if success:
        print(f"\n✅ TEST COMPLETADO EXITOSAMENTE")
    else:
        print(f"\n❌ TEST FALLÓ")
        sys.exit(1)