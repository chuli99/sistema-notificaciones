import logging
from database_config import db_config
from email_service import EmailService
from notification_actions_service import NotificationActionsService
import time
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_email_buttons_functionality():
    """
    Prueba completa de la funcionalidad de botones en emails
    """
    logger.info("🧪 Iniciando test de botones de email...")
    
    try:
        # 1. Verificar conexión a BD
        logger.info("1. Probando conexión a base de datos...")
        if not db_config.test_connection():
            logger.error("❌ Error de conexión a BD")
            return False
        logger.info("✅ Conexión a BD exitosa")
        
        # 2. Verificar estructura de BD
        logger.info("2. Verificando estructura de BD...")
        query = """
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'Notificaciones' 
        AND COLUMN_NAME IN ('status', 'action_token', 'expires_at', 'marked_received_at', 'cancelled_at')
        """
        columns = db_config.execute_query(query)
        required_columns = ['status', 'action_token', 'expires_at', 'marked_received_at', 'cancelled_at']
        existing_columns = [col['COLUMN_NAME'] for col in columns]
        
        missing_columns = [col for col in required_columns if col not in existing_columns]
        if missing_columns:
            logger.error(f"❌ Faltan columnas en BD: {missing_columns}")
            logger.info("Ejecuta el script migrations/add_action_buttons.sql")
            return False
        logger.info("✅ Estructura de BD correcta")
        
        # 3. Crear notificación de prueba
        logger.info("3. Creando notificación de prueba...")
        query_insert = """
        INSERT INTO Notificaciones (IdTipoNotificacion, Asunto, Cuerpo, Destinatario, Estado, Fecha_Programada)
        OUTPUT INSERTED.IdNotificacion
        VALUES (1, 'Test Botones Email', 'Esta es una notificación de prueba para validar los botones de email.', 'test@example.com', 'pendiente', GETDATE())
        """
        
        try:
            result = db_config.execute_query(query_insert)
            if result:
                test_notification_id = result[0]['IdNotificacion']
                logger.info(f"✅ Notificación de prueba creada ID: {test_notification_id}")
            else:
                # Fallback: buscar una notificación existente
                query_existing = "SELECT TOP 1 IdNotificacion FROM Notificaciones WHERE Estado = 'pendiente'"
                existing = db_config.execute_query(query_existing)
                if existing:
                    test_notification_id = existing[0]['IdNotificacion']
                    logger.info(f"✅ Usando notificación existente ID: {test_notification_id}")
                else:
                    logger.error("❌ No se pudo crear ni encontrar notificación de prueba")
                    return False
        except Exception as e:
            logger.warning(f"Usando método alternativo debido a: {e}")
            # Buscar notificación existente como fallback
            query_existing = "SELECT TOP 1 IdNotificación FROM Notificaciones ORDER BY IdNotificacion DESC"
            existing = db_config.execute_query(query_existing)
            if existing:
                test_notification_id = existing[0]['IdNotificacion']
                logger.info(f"✅ Usando notificación existente ID: {test_notification_id}")
            else:
                logger.error("❌ No hay notificaciones para probar")
                return False
        
        # 4. Probar EmailService
        logger.info("4. Probando EmailService...")
        email_service = EmailService()
        
        # Test configuración
        if not all([email_service.smtp_server, email_service.smtp_user, email_service.base_url]):
            logger.error("❌ Configuración SMTP incompleta")
            logger.info("Verifica SMTP_SERVER, SMTP_USER y BASE_URL en .env")
            return False
        
        logger.info(f"✅ EmailService configurado - Base URL: {email_service.base_url}")
        
        # Test generación de token
        token = email_service.generate_action_token()
        if len(token) < 20:
            logger.error("❌ Token muy corto")
            return False
        logger.info(f"✅ Token generado: {token[:10]}...")
        
        # Test construcción de email con botones
        original_body = "Contenido de prueba del email"
        email_with_buttons = email_service.build_email_with_actions(original_body, test_notification_id, token)
        
        if 'Marcar como Recibido' not in email_with_buttons:
            logger.error("❌ Botón 'Marcar como Recibido' no encontrado")
            return False
        
        if 'Anular Envío' not in email_with_buttons:
            logger.error("❌ Botón 'Anular Envío' no encontrado")
            return False
        
        logger.info("✅ Email con botones construido correctamente")
        
        # 5. Probar NotificationActionsService
        logger.info("5. Probando NotificationActionsService...")
        
        # Crear token válido primero
        expires_at = datetime.now() + timedelta(days=7)
        query_token = """
        UPDATE Notificaciones 
        SET action_token = ?, expires_at = ?, status = 'sent'
        WHERE IdNotificacion = ?
        """
        db_config.execute_non_query(query_token, [token, expires_at, test_notification_id])
        
        # Test marcar como recibido
        result = NotificationActionsService.mark_as_received(test_notification_id, token)
        if not result['success']:
            logger.error(f"❌ Error marcando como recibido: {result['message']}")
            return False
        logger.info("✅ Marcar como recibido funciona")
        
        # Resetear para probar cancelación
        new_token = email_service.generate_action_token()
        db_config.execute_non_query(query_token, [new_token, expires_at, test_notification_id])
        
        # Test cancelar
        result = NotificationActionsService.cancel_notification(test_notification_id, new_token)
        if not result['success']:
            logger.error(f"❌ Error cancelando: {result['message']}")
            return False
        logger.info("✅ Cancelar notificación funciona")
        
        # 6. Test de seguridad (token inválido)
        logger.info("6. Probando seguridad...")
        result = NotificationActionsService.mark_as_received(test_notification_id, "token_falso")
        if result['success']:
            logger.error("❌ PROBLEMA DE SEGURIDAD: Token falso aceptado")
            return False
        logger.info("✅ Seguridad: Token inválido rechazado correctamente")
        
        # 7. Test estadísticas
        logger.info("7. Probando estadísticas...")
        stats = NotificationActionsService.get_statistics()
        logger.info(f"✅ Estadísticas obtenidas: {len(stats)} estados")
        
        logger.info("🎉 TODOS LOS TESTS PASARON EXITOSAMENTE")
        logger.info("")
        logger.info("📋 Resumen de configuración:")
        logger.info(f"   - Base URL: {email_service.base_url}")
        logger.info(f"   - SMTP: {email_service.smtp_server}:{email_service.smtp_port}")
        logger.info(f"   - Notificación de prueba: ID {test_notification_id}")
        logger.info("")
        logger.info("🚀 Para usar en producción:")
        logger.info("   1. Ejecuta 'python web_server.py' para iniciar el servidor")
        logger.info("   2. Asegúrate de que BASE_URL sea accesible desde internet")
        logger.info("   3. Los emails incluirán automáticamente los botones")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en test: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Test de Funcionalidad - Botones de Email")
    print("=" * 50)
    
    success = test_email_buttons_functionality()
    
    print("=" * 50)
    if success:
        print("✅ TODOS LOS TESTS EXITOSOS")
        print("El sistema está listo para usar botones en emails.")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        print("Revisa los errores arriba y sigue las instrucciones.")
    
    print("\nPresiona Enter para continuar...")
    input()