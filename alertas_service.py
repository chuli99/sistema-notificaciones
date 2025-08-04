from database_config import db_config
import logging
from datetime import datetime
from email_service import EmailService

logger = logging.getLogger(__name__)
email_service = EmailService()

class ProcesadorNotificaciones:
    @staticmethod
    def procesar_pendientes():
        """
        Procesa todas las notificaciones pendientes y maneja el envío
        """
        logger.info("Iniciando procesamiento de notificaciones pendientes...")
        notificaciones = NotificacionesService.obtener_notificaciones_pendientes()
        
        if not notificaciones:
            logger.info("No hay notificaciones pendientes para procesar")
            return
        
        logger.info(f"Procesando {len(notificaciones)} notificaciones...")
        
        for notif in notificaciones:
            try:
                # Validación final
                if 'error' in notif:
                    raise ValueError(notif['error'])
                
                # Log con información de fecha programada
                fecha_prog_info = ""
                if notif['fecha_programada']:
                    fecha_prog_info = f" (programada para: {notif['fecha_programada']})"
                
                logger.info(f"Enviando notificación ID: {notif['IdNotificacion']} a {notif['destinatarios']}{fecha_prog_info}")
                
                # Enviar email a múltiples destinatarios
                destinatarios_lista = [email.strip() for email in notif['destinatarios'].split(',') if email.strip()]
                exitos = 0
                errores = []
                
                for destinatario in destinatarios_lista:
                    try:
                        exito_individual = email_service.enviar_email(
                            destinatario=destinatario,
                            asunto=notif['asunto'],
                            cuerpo=notif['cuerpo']
                        )
                        
                        if exito_individual:
                            exitos += 1
                            logger.info(f"Email enviado exitosamente a: {destinatario}")
                        else:
                            errores.append(f"Error enviando a {destinatario}")
                            
                    except Exception as e:
                        errores.append(f"Error enviando a {destinatario}: {str(e)}")
                        logger.error(f"Error enviando email a {destinatario}: {str(e)}")
                
                # Determinar si el envío fue exitoso (al menos uno exitoso)
                exito_general = exitos > 0
                
                if exito_general:
                    # Actualizar estado y auditoría
                    estado_mensaje = f"Enviado a {exitos}/{len(destinatarios_lista)} destinatarios"
                    if errores:
                        estado_mensaje += f". Errores: {'; '.join(errores)}"
                    
                    NotificacionesService.actualizar_estado_notificacion(
                        notif['IdNotificacion'], 'enviado' if not errores else 'parcial')
                    NotificacionesService.registrar_auditoria(
                        notif['IdNotificacion'], 
                        'NOTIFICACION_ENVIADA',
                        estado_mensaje
                    )
                    logger.info(f"Notificación {notif['IdNotificacion']} procesada: {estado_mensaje}")
                else:
                    raise Exception(f"Error al enviar a todos los destinatarios: {'; '.join(errores)}")
                
            except Exception as e:
                # Manejo de errores
                NotificacionesService.actualizar_estado_notificacion(
                    notif['IdNotificacion'], 'error')
                NotificacionesService.registrar_auditoria(
                    notif['IdNotificacion'],
                    'ERROR_NOTIFICACION',
                    f"Error: {str(e)}"
                )
                logger.error(f"Error procesando notificación {notif['IdNotificacion']}: {str(e)}")

class NotificacionesService:
    """
    Clase para manejar las operaciones relacionadas con el sistema de notificaciones.
    """
    
    @staticmethod
    def obtener_notificaciones_pendientes():
        """
        Se deben obtiener todas las notificaciones pendientes que no han sido enviadas.
        """
        query = """
        SELECT 
            n.IdNotificacion,
            n.IdTipoNotificacion,
            n.Asunto,
            n.Cuerpo,
            n.Destinatario,
            n.Estado,
            n.Fecha_Envio,
            n.Fecha_Programada,
            nt.descripcion as tipo_descripcion,
            nt.destinatarios as destinatarios_default,
            nt.asunto as asunto_default,
            nt.cuerpo as cuerpo_default
        FROM Notificaciones n
        LEFT JOIN Notificaciones_Tipo nt ON n.IdTipoNotificacion = nt.IdTipoNotificacion
        WHERE n.Estado = 'pendiente'
          AND (n.Fecha_Programada IS NULL OR n.Fecha_Programada <= GETDATE())
        ORDER BY n.Fecha_Programada ASC, n.Fecha_Envio ASC, n.IdNotificacion ASC
        """
        
        try:
            resultados = db_config.execute_query(query)
            
            # Procesar cada notificación para completar campos faltantes
            notificaciones_procesadas = []
            for notif in resultados:
                # Completar campos faltantes con los valores por defecto del tipo
                # Combinar destinatarios individuales y del tipo
                destinatarios_individuales = notif['Destinatario'] or ''
                destinatarios_tipo = notif['destinatarios_default'] or ''
                
                # Crear lista de destinatarios únicos
                todos_destinatarios = []
                if destinatarios_individuales.strip():
                    todos_destinatarios.extend([email.strip() for email in destinatarios_individuales.split(',') if email.strip()])
                if destinatarios_tipo.strip():
                    todos_destinatarios.extend([email.strip() for email in destinatarios_tipo.split(',') if email.strip()])
                
                # Eliminar duplicados manteniendo el orden
                destinatarios_unicos = []
                for email in todos_destinatarios:
                    if email not in destinatarios_unicos:
                        destinatarios_unicos.append(email)
                
                notif_procesada = {
                    'IdNotificacion': notif['IdNotificacion'],
                    'IdTipoNotificacion': notif['IdTipoNotificacion'],
                    'tipo_descripcion': notif['tipo_descripcion'] or 'Sin tipo',
                    'asunto': notif['Asunto'] or notif['asunto_default'] or 'Notificación del Sistema',
                    'cuerpo': notif['Cuerpo'] or notif['cuerpo_default'] or 'Tienes una nueva notificación del sistema.',
                    'destinatarios': ', '.join(destinatarios_unicos),
                    'estado': notif['Estado'],
                    'fecha_envio': notif['Fecha_Envio'],
                    'fecha_programada': notif['Fecha_Programada']
                }
                
                # Validar que tenga destinatarios
                if not notif_procesada['destinatarios'] or not notif_procesada['destinatarios'].strip():
                    notif_procesada['error'] = 'Sin destinatarios configurados'
                    logger.warning(f"Notificación {notif['IdNotificacion']} sin destinatarios - Tipo: {notif['IdTipoNotificacion']}")
                
                # Validar emails válidos (básico) - verificar que todos los emails contengan @
                elif notif_procesada['destinatarios']:
                    emails_invalidos = []
                    for email in notif_procesada['destinatarios'].split(', '):
                        if email.strip() and '@' not in email.strip():
                            emails_invalidos.append(email.strip())
                    
                    if emails_invalidos:
                        notif_procesada['error'] = f'Emails inválidos: {", ".join(emails_invalidos)}'
                        logger.warning(f"Notificación {notif['IdNotificacion']} con emails inválidos: {emails_invalidos}")
                
                notificaciones_procesadas.append(notif_procesada)
            
            logger.info(f"Se encontraron {len(notificaciones_procesadas)} notificaciones pendientes")
            return notificaciones_procesadas
            
        except Exception as e:
            logger.error(f"Error al obtener notificaciones pendientes: {e}")
            return []
    
    @staticmethod
    def actualizar_estado_notificacion(id_notificacion, nuevo_estado):
        """
        Actualiza el estado de una notificación.
        Estados posibles: 'pendiente', 'enviado', 'error'
        """
        query = """
        UPDATE Notificaciones 
        SET Estado = ?, Fecha_Envio = GETDATE()
        WHERE IdNotificacion = ?
        """
        
        try:
            db_config.execute_non_query(query, [nuevo_estado, id_notificacion])
            logger.info(f"Estado de notificación {id_notificacion} actualizado a: {nuevo_estado}")
            return True
        except Exception as e:
            logger.error(f"Error al actualizar estado de notificación {id_notificacion}: {e}")
            return False
    
    @staticmethod
    def registrar_auditoria(id_notificacion, accion, descripcion, usuario='sistema'):
        """
        Se debe registrar una entrada en la tabla de auditoría.
        """
        query = """
        INSERT INTO Auditoria (accion, detalle, fecha_aud, [user])
        VALUES (?, ?, GETDATE(), ?)
        """
        
        try:
            # Incluir el ID de notificación en el detalle para referencia
            detalle_completo = f"ID_Notificacion: {id_notificacion} - {descripcion}"
            
            db_config.execute_non_query(query, [accion, detalle_completo, usuario])
            logger.info(f"Auditoría registrada para notificación {id_notificacion}: {accion}")
            return True
        except Exception as e:
            logger.error(f"Error al registrar auditoría para notificación {id_notificacion}: {e}")
            return False
