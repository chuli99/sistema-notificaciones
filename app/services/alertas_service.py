from app.utils.database_config import db_config
import logging
from datetime import datetime
from app.services.email_service import EmailService
from app.services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)
email_service = EmailService()
whatsapp_service = WhatsAppService()

class ProcesadorNotificaciones:
    @staticmethod
    def procesar_pendientes():
        """
        Procesa todas las notificaciones pendientes y maneja el envío
        """
        logger.info("🚀 Iniciando procesamiento de notificaciones...")
        notificaciones = NotificacionesService.obtener_notificaciones_pendientes()
        
        if not notificaciones:
            logger.info("✅ No hay notificaciones pendientes")
            return
        
        logger.info(f"📧 Procesando {len(notificaciones)} notificaciones...")
        
        for notif in notificaciones:
            try:
                # Validación final
                if 'error' in notif:
                    raise ValueError(notif['error'])
                
                logger.info(f"Enviando ID {notif['IdNotificacion']} → {notif['destinatarios']}")
                
                # Función para procesar múltiples separadores (igual que arriba)
                def procesar_emails(texto_emails):
                    """Procesa emails separados por coma O punto y coma"""
                    if not texto_emails or not texto_emails.strip():
                        return []
                    
                    # Detectar el separador principal (punto y coma tiene prioridad)
                    if ';' in texto_emails:
                        separador = ';'
                    else:
                        separador = ','
                    
                    return [email.strip() for email in texto_emails.split(separador) if email.strip()]
                
                # Enviar email a múltiples destinatarios usando la función mejorada
                destinatarios_lista = procesar_emails(notif['destinatarios'])
                exitos = 0
                errores = []
                
                for destinatario in destinatarios_lista:
                    try:
                        exito_individual = email_service.enviar_email(
                            destinatario=destinatario,
                            asunto=notif['asunto'],
                            cuerpo=notif['cuerpo'],
                            notification_id=notif['IdNotificacion']  # Agregar ID para botones
                        )
                        
                        if exito_individual:
                            exitos += 1
                        else:
                            errores.append(f"Error enviando a {destinatario}")
                            
                    except Exception as e:
                        errores.append(f"Error enviando a {destinatario}: {str(e)}")
                        logger.error(f"❌ Error enviando a {destinatario}: {str(e)}")
                
                # Determinar si el envío fue exitoso (al menos uno exitoso)
                exito_general = exitos > 0
                
                if exito_general:
                    # Actualizar estado y auditoría
                    estado_final = 'enviado' if not errores else 'parcial'
                    estado_mensaje = f"{exitos}/{len(destinatarios_lista)} enviados"
                    
                    NotificacionesService.actualizar_estado_notificacion(
                        notif['IdNotificacion'], estado_final)
                    NotificacionesService.registrar_auditoria(
                        notif['IdNotificacion'], 
                        'NOTIFICACION_ENVIADA',
                        estado_mensaje
                    )
                    logger.info(f"✅ ID {notif['IdNotificacion']}: {estado_mensaje}")
                else:
                    raise Exception(f"Falló envío a todos los destinatarios")
                
            except Exception as e:
                # Manejo de errores
                NotificacionesService.actualizar_estado_notificacion(
                    notif['IdNotificacion'], 'error')
                NotificacionesService.registrar_auditoria(
                    notif['IdNotificacion'],
                    'ERROR_NOTIFICACION',
                    f"Error: {str(e)}"
                )
                logger.error(f"❌ ID {notif['IdNotificacion']}: {str(e)}")
    
    @staticmethod
    def procesar_whatsapp_pendientes():
        """
        Procesa todas las notificaciones de WhatsApp pendientes y maneja el envío
        """
        logger.info("🚀 Iniciando procesamiento de notificaciones de WhatsApp...")
        notificaciones = NotificacionesService.obtener_notificaciones_whatsapp_pendientes()
        
        if not notificaciones:
            logger.info("✅ No hay notificaciones de WhatsApp pendientes")
            return
        
        logger.info(f"📱 Procesando {len(notificaciones)} notificaciones de WhatsApp...")
        
        for notif in notificaciones:
            try:
                # Validación final
                if 'error' in notif:
                    raise ValueError(notif['error'])
                
                logger.info(f"Enviando WhatsApp ID {notif['IdNotificacion']} → {notif['destinatario']}")
                
                # Enviar WhatsApp (sin botones, solo informativo)
                exito = whatsapp_service.enviar_notificacion(
                    destinatario=notif['destinatario'],
                    asunto=notif['asunto'],
                    cuerpo=notif['cuerpo']
                )
                
                if exito:
                    # Actualizar estado y auditoría
                    NotificacionesService.actualizar_estado_notificacion(
                        notif['IdNotificacion'], 'enviado')
                    NotificacionesService.registrar_auditoria(
                        notif['IdNotificacion'], 
                        'NOTIFICACION_WHATSAPP_ENVIADA',
                        f"Enviado a {notif['destinatario']}"
                    )
                    logger.info(f"✅ WhatsApp ID {notif['IdNotificacion']}: Enviado exitosamente")
                else:
                    raise Exception(f"Falló envío de WhatsApp a {notif['destinatario']}")
                
            except Exception as e:
                # Manejo de errores
                NotificacionesService.actualizar_estado_notificacion(
                    notif['IdNotificacion'], 'error')
                NotificacionesService.registrar_auditoria(
                    notif['IdNotificacion'],
                    'ERROR_NOTIFICACION_WHATSAPP',
                    f"Error: {str(e)}"
                )
                logger.error(f"❌ WhatsApp ID {notif['IdNotificacion']}: {str(e)}")

class NotificacionesService:
    """
    Clase para manejar las operaciones relacionadas con el sistema de notificaciones.
    """
    
    @staticmethod
    def obtener_notificaciones_pendientes():
        """
        Obtiene notificaciones que están programadas para HOY (o anterior) y están pendientes.
        LÓGICA OPTIMIZADA: PRIMERO verifica la fecha (solo día, ignora hora), LUEGO verifica el estado, FINALMENTE el medio.
        Esto es más intuitivo para usuarios que seleccionan solo fechas en el dashboard.
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
            n.Medio,
            nt.descripcion as tipo_descripcion,
            nt.destinatarios as destinatarios_default,
            nt.asunto as asunto_default,
            nt.cuerpo as cuerpo_default
        FROM Notificaciones n
        LEFT JOIN Notificaciones_Tipo nt ON n.IdTipoNotificacion = nt.IdTipoNotificacion
        WHERE (n.Fecha_Programada IS NULL OR CAST(n.Fecha_Programada AS DATE) <= CAST(GETDATE() AS DATE))  -- FILTRO PRIMARIO: Solo fechas válidas (hoy o anterior - sin hora)
          AND n.Estado = 'pendiente'  -- FILTRO SECUNDARIO: Solo notificaciones pendientes
          AND (n.Medio = 'Email' OR n.Medio IS NULL)  -- FILTRO TERCIARIO: Solo medio Email (o NULL por defecto)
        ORDER BY 
            CASE WHEN n.Fecha_Programada IS NULL THEN 0 ELSE 1 END,  -- Prioridad: inmediatas primero
            n.Fecha_Programada ASC,  -- Luego por fecha programada
            n.IdNotificacion ASC     -- Finalmente por ID
        """
        
        try:
            logger.info("🔍 Buscando notificaciones pendientes para hoy (solo fecha, ignora hora)...")
            
            resultados = db_config.execute_query(query)
            
            if not resultados:
                logger.info("ℹ️ No hay notificaciones pendientes para procesar")
                return []
            
            logger.info(f"📋 Encontradas {len(resultados)} notificaciones para procesar")
            
            # Procesar cada notificación para completar campos faltantes
            notificaciones_procesadas = []
            for notif in resultados:
                
                # VALIDACIÓN EXTRA: Verificar que realmente esté pendiente
                if notif['Estado'] != 'pendiente':
                    logger.error(f"🚨 Notificación {notif['IdNotificacion']} tiene estado '{notif['Estado']}' - SALTANDO")
                    continue
                
                # Combinar destinatarios individuales y del tipo
                destinatarios_individuales = notif['Destinatario'] or ''
                destinatarios_tipo = notif['destinatarios_default'] or ''
                
                # Función para procesar múltiples separadores
                def procesar_destinatarios(texto_destinatarios):
                    """Procesa destinatarios separados por coma O punto y coma"""
                    if not texto_destinatarios or not texto_destinatarios.strip():
                        return []
                    
                    # Detectar el separador principal (punto y coma tiene prioridad)
                    if ';' in texto_destinatarios:
                        separador = ';'
                    else:
                        separador = ','
                    
                    return [email.strip() for email in texto_destinatarios.split(separador) if email.strip()]
                
                # Crear lista de destinatarios únicos usando la función mejorada
                todos_destinatarios = []
                todos_destinatarios.extend(procesar_destinatarios(destinatarios_individuales))
                todos_destinatarios.extend(procesar_destinatarios(destinatarios_tipo))
                
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
    def obtener_notificaciones_whatsapp_pendientes():
        """
        Obtiene notificaciones de WhatsApp que están programadas para HOY (o anterior) y están pendientes.
        Similar a obtener_notificaciones_pendientes pero filtra por medio WhatsApp.
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
            n.Medio,
            nt.descripcion as tipo_descripcion,
            nt.asunto as asunto_default,
            nt.cuerpo as cuerpo_default
        FROM Notificaciones n
        LEFT JOIN Notificaciones_Tipo nt ON n.IdTipoNotificacion = nt.IdTipoNotificacion
        WHERE (n.Fecha_Programada IS NULL OR CAST(n.Fecha_Programada AS DATE) <= CAST(GETDATE() AS DATE))
          AND n.Estado = 'pendiente'
          AND n.Medio = 'Whatsapp'  -- Solo WhatsApp
        ORDER BY 
            CASE WHEN n.Fecha_Programada IS NULL THEN 0 ELSE 1 END,
            n.Fecha_Programada ASC,
            n.IdNotificacion ASC
        """
        
        try:
            logger.info("🔍 Buscando notificaciones de WhatsApp pendientes...")
            
            resultados = db_config.execute_query(query)
            
            if not resultados:
                logger.info("ℹ️ No hay notificaciones de WhatsApp pendientes")
                return []
            
            logger.info(f"📋 Encontradas {len(resultados)} notificaciones de WhatsApp")
            
            notificaciones_procesadas = []
            for notif in resultados:
                
                # VALIDACIÓN: Verificar que esté pendiente
                if notif['Estado'] != 'pendiente':
                    logger.error(f"🚨 Notificación {notif['IdNotificacion']} tiene estado '{notif['Estado']}' - SALTANDO")
                    continue
                
                # Para WhatsApp, el destinatario es un número de teléfono (NO múltiples)
                destinatario = (notif['Destinatario'] or '').strip()
                
                notif_procesada = {
                    'IdNotificacion': notif['IdNotificacion'],
                    'IdTipoNotificacion': notif['IdTipoNotificacion'],
                    'tipo_descripcion': notif['tipo_descripcion'] or 'Sin tipo',
                    'asunto': notif['Asunto'] or notif['asunto_default'] or 'Notificación del Sistema',
                    'cuerpo': notif['Cuerpo'] or notif['cuerpo_default'] or 'Tienes una nueva notificación del sistema.',
                    'destinatario': destinatario,
                    'estado': notif['Estado'],
                    'fecha_envio': notif['Fecha_Envio'],
                    'fecha_programada': notif['Fecha_Programada'],
                    'medio': notif['Medio']
                }
                
                # Validar que tenga destinatario
                if not destinatario:
                    notif_procesada['error'] = 'Sin número de teléfono configurado'
                    logger.warning(f"Notificación {notif['IdNotificacion']} sin destinatario")
                
                # Validar formato de número (debe empezar con +)
                elif not destinatario.startswith('+'):
                    notif_procesada['error'] = f'Número debe incluir código de país: {destinatario}'
                    logger.warning(f"Notificación {notif['IdNotificacion']} con número inválido: {destinatario}")
                
                notificaciones_procesadas.append(notif_procesada)
            
            logger.info(f"Se encontraron {len(notificaciones_procesadas)} notificaciones de WhatsApp pendientes")
            return notificaciones_procesadas
            
        except Exception as e:
            logger.error(f"Error al obtener notificaciones de WhatsApp: {e}")
            return []
    
    @staticmethod
    def actualizar_estado_notificacion(id_notificacion, nuevo_estado):
        """
        Actualiza el estado de una notificación de forma segura.
        Solo permite cambios desde estado 'pendiente' a otros estados.
        Estados válidos: 'pendiente' → 'enviado', 'error', 'parcial'
        """
        # Primero verificar el estado actual
        query_verificar = """
        SELECT Estado, Fecha_Programada, Asunto 
        FROM Notificaciones 
        WHERE IdNotificacion = ?
        """
        
        try:
            resultado_actual = db_config.execute_query(query_verificar, [id_notificacion])
            
            if not resultado_actual:
                logger.error(f"❌ Notificación {id_notificacion} no encontrada")
                return False
            
            estado_previo = resultado_actual[0]['Estado']
            fecha_prog = resultado_actual[0]['Fecha_Programada']
            asunto = resultado_actual[0]['Asunto']
            
            # VALIDACIÓN CRÍTICA: Solo permitir cambios desde 'pendiente'
            if estado_previo != 'pendiente':
                logger.warning(f"🚨 ID {id_notificacion}: No se puede cambiar estado '{estado_previo}' → '{nuevo_estado}'")
                return False
            
            # Actualizar solo si el estado actual es 'pendiente'
            query_actualizar = """
            UPDATE Notificaciones 
            SET Estado = ?, Fecha_Envio = GETDATE()
            WHERE IdNotificacion = ? AND Estado = 'pendiente'
            """
            
            filas_afectadas = db_config.execute_non_query(query_actualizar, [nuevo_estado, id_notificacion])
            
            if filas_afectadas > 0:
                return True
            else:
                logger.warning(f"⚠️ No se pudo actualizar ID {id_notificacion} - Estado cambió")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error actualizando ID {id_notificacion}: {e}")
            return False
    
    @staticmethod
    def registrar_auditoria(id_notificacion, accion, descripcion, usuario='sistema'):
        """
        Registra entrada en auditoría
        """
        query = """
        INSERT INTO Auditoria (accion, detalle, fecha_aud, [user])
        VALUES (?, ?, GETDATE(), ?)
        """
        
        try:
            detalle_completo = f"ID_{id_notificacion}: {descripcion}"
            db_config.execute_non_query(query, [accion, detalle_completo, usuario])
            return True
        except Exception as e:
            logger.error(f"❌ Error en auditoría ID {id_notificacion}: {e}")
            return False
