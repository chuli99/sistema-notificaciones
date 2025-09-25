from app.utils.database_config import db_config
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationActionsService:
    """
    Servicio para manejar las acciones de los botones en los emails
    """
    
    @staticmethod
    def mark_as_received(notification_id, token):
        """
        Marca una notificación como recibida usando el token de seguridad
        """
        try:
            # Verificar token válido y no expirado
            query_verify = """
            SELECT IdNotificacion, Estado, expires_at, Asunto
            FROM Notificaciones 
            WHERE IdNotificacion = ? 
              AND action_token = ? 
              AND expires_at > GETDATE()
              AND Estado = 'enviado'
            """
            
            result = db_config.execute_query(query_verify, [notification_id, token])
            
            if not result:
                logger.warning(f"Token inválido o expirado para notificación {notification_id}")
                return {
                    'success': False, 
                    'message': 'Token inválido o expirado',
                    'type': 'error'
                }
            
            # Actualizar estado a "recibido"
            query_update = """
            UPDATE Notificaciones 
            SET Estado = 'recibido', 
                marked_received_at = GETDATE()
            WHERE IdNotificacion = ? AND action_token = ?
            """
            
            rows_affected = db_config.execute_non_query(query_update, [notification_id, token])
            
            if rows_affected > 0:
                # Registrar en auditoría
                NotificationActionsService.log_action(
                    notification_id, 
                    'MARKED_RECEIVED', 
                    'Usuario marcó notificación como recibida'
                )
                
                logger.info(f"✅ Notificación {notification_id} marcada como recibida")
                return {
                    'success': True,
                    'message': '✅ Notificación marcada como recibida correctamente',
                    'type': 'success'
                }
            else:
                return {
                    'success': False,
                    'message': 'No se pudo actualizar la notificación',
                    'type': 'error'
                }
                
        except Exception as e:
            logger.error(f"Error marcando notificación {notification_id} como recibida: {e}")
            return {
                'success': False,
                'message': 'Error interno del sistema',
                'type': 'error'
            }
    
    @staticmethod
    def cancel_notification(notification_id, token):
        """
        Cancela una notificación usando el token de seguridad.
        Cuando una notificación se cancela, también cancela todas las notificaciones
        con el mismo Source_IdNotificacion.
        """
        try:
            # Verificar token válido y no expirado
            query_verify = """
            SELECT IdNotificacion, Estado, expires_at, Asunto, Source_IdNotificacion
            FROM Notificaciones 
            WHERE IdNotificacion = ? 
              AND action_token = ? 
              AND expires_at > GETDATE()
              AND Estado = 'enviado'
            """
            
            result = db_config.execute_query(query_verify, [notification_id, token])
            
            if not result:
                logger.warning(f"Token inválido o expirado para notificación {notification_id}")
                return {
                    'success': False, 
                    'message': 'Token inválido o expirado',
                    'type': 'error'
                }
            
            notification_data = result[0]
            source_id = notification_data['Source_IdNotificacion']
            
            # Cancelar la notificación principal
            query_update_main = """
            UPDATE Notificaciones 
            SET Estado = 'cancelado', 
                cancelled_at = GETDATE()
            WHERE IdNotificacion = ? AND action_token = ?
            """
            
            rows_affected = db_config.execute_non_query(query_update_main, [notification_id, token])
            
            if rows_affected > 0:
                # Cancelar todas las notificaciones relacionadas con el mismo Source_IdNotificacion
                related_cancelled = 0
                if source_id is not None:
                    query_update_related = """
                    UPDATE Notificaciones 
                    SET Estado = 'cancelado', 
                        cancelled_at = GETDATE()
                    WHERE Source_IdNotificacion = ? 
                      AND Estado != 'cancelado'
                      AND IdNotificacion != ?
                    """
                    
                    related_cancelled = db_config.execute_non_query(query_update_related, [source_id, notification_id])
                    
                    if related_cancelled > 0:
                        logger.info(f"✅ Se cancelaron {related_cancelled} notificaciones relacionadas con Source_IdNotificacion: {source_id}")
                
                # Registrar en auditoría la cancelación principal
                NotificationActionsService.log_action(
                    notification_id, 
                    'NOTIFICATION_CANCELLED', 
                    f'Usuario canceló la notificación. Source_IdNotificacion: {source_id}'
                )
                
                # Registrar en auditoría las cancelaciones relacionadas si las hubo
                if related_cancelled > 0:
                    NotificationActionsService.log_action(
                        notification_id, 
                        'RELATED_NOTIFICATIONS_CANCELLED', 
                        f'Se cancelaron {related_cancelled} notificaciones relacionadas con Source_IdNotificacion: {source_id}'
                    )
                
                # Preparar mensaje de respuesta
                total_cancelled = 1 + related_cancelled
                if related_cancelled > 0:
                    message = f'❌ Notificación cancelada correctamente. También se cancelaron {related_cancelled} notificaciones relacionadas (Total: {total_cancelled})'
                else:
                    message = '❌ Notificación cancelada correctamente'
                
                logger.info(f"Notificación {notification_id} cancelada (relacionadas: {related_cancelled})")
                return {
                    'success': True,
                    'message': message,
                    'type': 'success',
                    'related_cancelled': related_cancelled,
                    'total_cancelled': total_cancelled
                }
            else:
                return {
                    'success': False,
                    'message': 'No se pudo cancelar la notificación',
                    'type': 'error'
                }
                
        except Exception as e:
            logger.error(f"Error cancelando notificación {notification_id}: {e}")
            return {
                'success': False,
                'message': 'Error interno del sistema',
                'type': 'error'
            }
    
    @staticmethod
    def get_notification_status(notification_id):
        """
        Obtiene el estado actual de una notificación
        """
        try:
            query = """
            SELECT IdNotificacion, Estado, marked_received_at, cancelled_at, 
                   expires_at, Asunto, Destinatario
            FROM Notificaciones 
            WHERE IdNotificacion = ?
            """
            
            result = db_config.execute_query(query, [notification_id])
            
            if result:
                return result[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo estado de notificación {notification_id}: {e}")
            return None
    
    @staticmethod
    def log_action(notification_id, action, description):
        """
        Registra la acción en la tabla de auditoría
        """
        try:
            query = """
            INSERT INTO Auditoria (accion, detalle, fecha_aud, [user])
            VALUES (?, ?, GETDATE(), 'user_action')
            """
            
            detail = f"ID_{notification_id}: {description}"
            db_config.execute_non_query(query, [action, detail])
            
        except Exception as e:
            logger.error(f"Error registrando acción en auditoría: {e}")
    
    @staticmethod
    def get_statistics():
        """
        Obtiene estadísticas de las acciones realizadas
        """
        try:
            query = """
            SELECT 
                Estado,
                COUNT(*) as count,
                COUNT(CASE WHEN marked_received_at IS NOT NULL THEN 1 END) as received_count,
                COUNT(CASE WHEN cancelled_at IS NOT NULL THEN 1 END) as cancelled_count
            FROM Notificaciones 
            WHERE action_token IS NOT NULL
            GROUP BY Estado
            """
            
            return db_config.execute_query(query)
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return []