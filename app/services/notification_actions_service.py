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
        Permite múltiples destinatarios con el mismo token
        """
        try:
            # Verificar token válido y no expirado
            # Permitir si está en estado 'enviado' o si ya está 'recibido' (para múltiples destinatarios)
            query_verify = """
            SELECT IdNotificacion, Estado, FechaExpiracion, Asunto
            FROM Notificaciones 
            WHERE IdNotificacion = ? 
              AND TokenRespuesta = ? 
              AND FechaExpiracion > GETDATE()
              AND Estado IN ('enviado', 'recibido')
            """
            
            result = db_config.execute_query(query_verify, [notification_id, token])
            
            if not result:
                logger.warning(f"Token inválido o expirado para notificación {notification_id}")
                return {
                    'success': False, 
                    'message': 'Token inválido o expirado',
                    'type': 'error'
                }
            
            # Si ya está marcado como recibido, solo registrar la acción sin cambiar estado
            current_state = result[0]['Estado']
            
            if current_state == 'recibido':
                # Ya está marcado como recibido por otro destinatario
                logger.info(f"✅ Notificación {notification_id} ya estaba marcada como recibida")
                return {
                    'success': True,
                    'message': '✅ Notificación ya estaba marcada como recibida',
                    'type': 'success'
                }
            
            # Actualizar estado a "recibido" solo si no estaba ya marcado
            query_update = """
            UPDATE Notificaciones 
            SET Estado = 'recibido', 
                FechaRecibido = CASE WHEN FechaRecibido IS NULL THEN GETDATE() ELSE FechaRecibido END
            WHERE IdNotificacion = ? AND TokenRespuesta = ? AND Estado = 'enviado'
            """
            
            rows_affected = db_config.execute_non_query(query_update, [notification_id, token])
            
            if rows_affected >= 0:  # Cambio: >= 0 en lugar de > 0 para manejar casos donde ya estaba marcado
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
    def mark_as_resolved(notification_id, token):
        """
        Marca una notificación como resuelta usando el token de seguridad.
        Permite múltiples destinatarios con el mismo token.
        Cuando una notificación se marca como resuelta, actualiza automáticamente todas las 
        notificaciones PENDIENTES que tengan el mismo IdAlerta.
        """
        try:
            # Verificar token válido y no expirado
            # Permitir si está en estado 'enviado', 'recibido' o ya 'resuelto' (para múltiples destinatarios)
            query_verify = """
            SELECT IdNotificacion, Estado, FechaExpiracion, Asunto, IdAlerta
            FROM Notificaciones 
            WHERE IdNotificacion = ? 
              AND TokenRespuesta = ? 
              AND FechaExpiracion > GETDATE()
              AND Estado IN ('enviado', 'recibido', 'resuelto', 'cancelado')
            """
            
            result = db_config.execute_query(query_verify, [notification_id, token])
            
            if not result:
                logger.warning(f"Token inválido o expirado para notificación {notification_id}")
                return {
                    'success': False, 
                    'message': 'El enlace ha expirado o no es válido',
                    'type': 'error'
                }
            
            notification_data = result[0]
            current_state = notification_data['Estado']
            id_alerta = notification_data['IdAlerta']
            
            # Si ya está marcado como resuelto, solo registrar la acción sin cambiar estado
            if current_state == 'resuelto':
                # Ya está marcado como resuelto por otro destinatario
                logger.info(f"✅ Notificación {notification_id} ya estaba marcada como resuelta")
                return {
                    'success': True,
                    'message': '✅ Notificación ya estaba marcada como resuelta',
                    'type': 'success'
                }
            
            # Actualizar estado a "resuelto" solo si no estaba ya marcado
            query_update = """
            UPDATE Notificaciones 
            SET Estado = 'resuelto', 
                FechaResuelto = CASE WHEN FechaResuelto IS NULL THEN GETDATE() ELSE FechaResuelto END
            WHERE IdNotificacion = ? AND TokenRespuesta = ? AND Estado IN ('enviado', 'recibido', 'cancelado')
            """
            
            rows_affected = db_config.execute_non_query(query_update, [notification_id, token])
            
            # NUEVA LÓGICA: Actualizar todas las notificaciones PENDIENTES con el mismo IdAlerta
            related_resolved = 0
            if id_alerta is not None:
                logger.info(f"🔄 Actualizando notificaciones PENDIENTES con IdAlerta: {id_alerta}")
                
                query_update_related = """
                UPDATE Notificaciones 
                SET Estado = 'resuelto', 
                    FechaResuelto = GETDATE()
                WHERE IdAlerta = ? 
                  AND Estado = 'pendiente'
                  AND IdNotificacion != ?
                """
                
                related_resolved = db_config.execute_non_query(query_update_related, [id_alerta, notification_id])
                
                if related_resolved > 0:
                    logger.info(f"✅ Se marcaron como resueltas {related_resolved} notificaciones PENDIENTES con IdAlerta: {id_alerta}")
                    
                    # Registrar en auditoría las actualizaciones relacionadas
                    NotificationActionsService.log_action(
                        notification_id, 
                        'ALERTAS_PENDIENTES_RESUELTAS', 
                        f'Se resolvieron {related_resolved} notificaciones pendientes con IdAlerta: {id_alerta}'
                    )
                else:
                    logger.info(f"ℹ️ No se encontraron notificaciones pendientes para resolver con IdAlerta: {id_alerta}")
            
            if rows_affected >= 0:  # Cambio: >= 0 en lugar de > 0 para manejar casos donde ya estaba marcado
                # Registrar en auditoría la acción principal
                NotificationActionsService.log_action(
                    notification_id, 
                    'NOTIFICACION_RESUELTA',
                    f"Notificación marcada como resuelta: {notification_data['Asunto']}"
                )
                
                # Preparar mensaje de respuesta
                total_resolved = 1 + related_resolved
                if related_resolved > 0:
                    message = f'✅ Notificación marcada como resuelta correctamente. También se resolvieron {related_resolved} notificaciones pendientes.'
                else:
                    message = '✅ La notificación ha sido marcada como resuelta correctamente'
                
                logger.info(f"Notificación {notification_id} marcada como resuelta exitosamente (pendientes resueltas: {related_resolved})")
                return {
                    'success': True,
                    'message': message,
                    'type': 'success',
                    'related_resolved': related_resolved,
                    'total_resolved': total_resolved
                }
            else:
                return {
                    'success': False,
                    'message': 'No se pudo actualizar la notificación',
                    'type': 'error'
                }
                
        except Exception as e:
            logger.error(f"Error marcando notificación {notification_id} como resuelta: {e}")
            return {
                'success': False,
                'message': 'Error interno del sistema',
                'type': 'error'
            }
    
    @staticmethod
    def cancel_notification(notification_id, token):
        """
        Cancela una notificación usando el token de seguridad.
        Permite múltiples destinatarios con el mismo token.
        Cuando una notificación se cancela, también cancela todas las notificaciones
        con el mismo Source_IdNotificacion (lógica existente) o IdAlerta (nueva lógica).
        """
        try:
            # Verificar token válido y no expirado
            # Permitir cancelación incluso si ya está cancelada (para múltiples destinatarios)
            query_verify = """
            SELECT IdNotificacion, Estado, FechaExpiracion, Asunto, Source_IdNotificacion, IdAlerta
            FROM Notificaciones 
            WHERE IdNotificacion = ? 
              AND TokenRespuesta = ? 
              AND FechaExpiracion > GETDATE()
              AND Estado IN ('enviado', 'recibido', 'cancelado', 'resuelto')
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
            current_state = notification_data['Estado']
            source_id = notification_data['Source_IdNotificacion']
            id_alerta = notification_data['IdAlerta']
            
            # Si ya está cancelada, solo registrar la acción sin cambiar estado
            if current_state == 'cancelado':
                logger.info(f"✅ Notificación {notification_id} ya estaba cancelada")
                return {
                    'success': True,
                    'message': '✅ Notificación ya estaba cancelada',
                    'type': 'success'
                }
            
            # Cancelar la notificación principal solo si no estaba cancelada
            query_update_main = """
            UPDATE Notificaciones 
            SET Estado = 'cancelado', 
                FechaCancelacion = CASE WHEN FechaCancelacion IS NULL THEN GETDATE() ELSE FechaCancelacion END
            WHERE IdNotificacion = ? AND TokenRespuesta = ? AND Estado IN ('enviado', 'recibido', 'resuelto')
            """
            
            rows_affected = db_config.execute_non_query(query_update_main, [notification_id, token])
            
            related_cancelled = 0
            
            if rows_affected >= 0:  # Cambio: >= 0 en lugar de > 0 para manejar casos donde ya estaba marcado
                
                # LÓGICA EXISTENTE: Cancelar por Source_IdNotificacion (solo pendientes)
                if source_id is not None:
                    query_update_related = """
                    UPDATE Notificaciones 
                    SET Estado = 'cancelado', 
                        FechaCancelacion = GETDATE()
                    WHERE Source_IdNotificacion = ? 
                      AND Estado = 'pendiente'
                      AND IdNotificacion != ?
                    """
                    
                    source_cancelled = db_config.execute_non_query(query_update_related, [source_id, notification_id])
                    related_cancelled += source_cancelled
                    
                    if source_cancelled > 0:
                        logger.info(f"✅ Se cancelaron {source_cancelled} notificaciones relacionadas por Source_IdNotificacion: {source_id}")
                
                # NUEVA LÓGICA: Cancelar todas las notificaciones PENDIENTES con el mismo IdAlerta
                if id_alerta is not None:
                    logger.info(f"🔄 Cancelando notificaciones PENDIENTES con IdAlerta: {id_alerta}")
                    
                    query_cancel_by_alerta = """
                    UPDATE Notificaciones 
                    SET Estado = 'cancelado', 
                        FechaCancelacion = GETDATE()
                    WHERE IdAlerta = ? 
                      AND Estado = 'pendiente'
                      AND IdNotificacion != ?
                    """
                    
                    alerta_cancelled = db_config.execute_non_query(query_cancel_by_alerta, [id_alerta, notification_id])
                    related_cancelled += alerta_cancelled
                    
                    if alerta_cancelled > 0:
                        logger.info(f"✅ Se cancelaron {alerta_cancelled} notificaciones PENDIENTES con IdAlerta: {id_alerta}")
                        
                        # Registrar en auditoría las cancelaciones por IdAlerta
                        NotificationActionsService.log_action(
                            notification_id, 
                            'ALERTAS_PENDIENTES_CANCELADAS', 
                            f'Se cancelaron {alerta_cancelled} notificaciones pendientes con IdAlerta: {id_alerta}'
                        )
                    else:
                        logger.info(f"ℹ️ No se encontraron notificaciones pendientes para cancelar con IdAlerta: {id_alerta}")
                
                # Registrar en auditoría la cancelación principal
                NotificationActionsService.log_action(
                    notification_id, 
                    'NOTIFICATION_CANCELLED', 
                    f'Usuario canceló la notificación. Source_IdNotificacion: {source_id}, IdAlerta: {id_alerta}'
                )
                
                # Preparar mensaje de respuesta
                total_cancelled = 1 + related_cancelled
                if related_cancelled > 0:
                    message = f'❌ Notificación cancelada correctamente. También se cancelaron {related_cancelled} notificaciones/alertas relacionadas'
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
            SELECT IdNotificacion, Estado, FechaRecibido, FechaCancelacion, 
                   FechaExpiracion, FechaResuelto, Asunto, Destinatario
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
                COUNT(CASE WHEN FechaRecibido IS NOT NULL THEN 1 END) as received_count,
                COUNT(CASE WHEN FechaResuelto IS NOT NULL THEN 1 END) as resolved_count,
                COUNT(CASE WHEN FechaCancelacion IS NOT NULL THEN 1 END) as cancelled_count
            FROM Notificaciones 
            WHERE TokenRespuesta IS NOT NULL
            GROUP BY Estado
            """
            
            return db_config.execute_query(query)
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return []