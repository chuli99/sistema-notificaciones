import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
import logging
import os
import secrets
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app.utils.database_config import db_config

logger = logging.getLogger(__name__)
load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.sender_name = os.getenv('EMAIL_SENDER_NAME', 'Sistema de Notificaciones')
        self.base_url = os.getenv('BASE_URL')

    def enviar_email(self, destinatario, asunto, cuerpo, notification_id=None):
        """
        Intenta enviar un email y retorna True si tiene éxito
        Ahora incluye botones de acción si se proporciona notification_id
        """
        if not all([self.smtp_server, self.smtp_user, self.smtp_password]):
            logger.error("Configuración SMTP incompleta en variables de entorno")
            return False

        try:
            logger.info(f"🔍 Conectando SMTP {self.smtp_server}:{self.smtp_port}")
            
            # Obtener o generar token para la notificación
            if notification_id:
                token_respuesta = self.get_or_create_action_token(notification_id)
                
                # Agregar botones al cuerpo del email
                cuerpo = self.build_email_with_actions(cuerpo, notification_id, token_respuesta)
            
            msg = MIMEText(cuerpo, 'html')
            msg['Subject'] = asunto
            msg['From'] = formataddr(("Sistema de Notificaciones", os.getenv('SMTP_USER'))) #Aqui deben cambiar con la config del servidor SMTP
            msg['To'] = destinatario

            # SOLUCION: Agregar timeout de 30 segundos
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, destinatario, msg.as_string())
            
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ Error de autenticación SMTP: {str(e)}")
            return False
        except smtplib.SMTPConnectError as e:
            logger.error(f"❌ Error de conexión SMTP: {str(e)}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ Error SMTP general: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Error enviando email a {destinatario}: {str(e)}")
            return False
    
    def generate_action_token(self):
        """Genera un token seguro para las acciones de email"""
        return secrets.token_urlsafe(32)
    
    def get_or_create_action_token(self, notification_id):
        """
        Obtiene el token existente para una notificación o crea uno nuevo si no existe.
        PRIMERO verifica si existe, LUEGO genera uno nuevo solo si es necesario.
        """
        try:
            # PASO 1: Verificar si ya existe un token en la base de datos
            query_check_existing = """
            SELECT TokenRespuesta, FechaExpiracion 
            FROM Notificaciones 
            WHERE IdNotificacion = ? AND TokenRespuesta IS NOT NULL
            """
            
            result = db_config.execute_query(query_check_existing, [notification_id])
            
            if result and len(result) > 0:
                # YA EXISTE UN TOKEN - reutilizarlo
                existing_token = result[0]['TokenRespuesta']
                logger.info(f"✅ Reutilizando token existente para notificación {notification_id}: {existing_token[:10]}...")
                return existing_token
            
            # PASO 2: No existe token, crear uno nuevo
            logger.info(f"🔑 No existe token para notificación {notification_id}, creando uno nuevo...")
            nuevo_token = self.generate_action_token()
            fecha_expiracion = datetime.now() + timedelta(days=7)
            
            # Guardar el nuevo token en la base de datos
            self.save_action_token(notification_id, nuevo_token, fecha_expiracion)
            
            logger.info(f"🔑 Nuevo token creado para notificación {notification_id}: {nuevo_token[:10]}...")
            return nuevo_token
                
        except Exception as e:
            logger.error(f"Error obteniendo/creando token para notificación {notification_id}: {e}")
            # Fallback: generar token temporal
            return self.generate_action_token()
    
    def save_action_token(self, notification_id, token, fecha_expiracion):
        """Guarda el token de acción en la base de datos SOLO si no existe ya uno"""
        try:
            # Solo actualizar si TokenRespuesta es NULL (no existe todavía)
            query = """
            UPDATE Notificaciones 
            SET TokenRespuesta = ?, FechaExpiracion = ?
            WHERE IdNotificacion = ? AND TokenRespuesta IS NULL
            """
            rows_affected = db_config.execute_non_query(query, [token, fecha_expiracion, notification_id])
            
            if rows_affected > 0:
                logger.info(f"✅ Token guardado para notificación {notification_id}")
            else:
                logger.info(f"ℹ️ Token ya existía para notificación {notification_id}, no se sobrescribió")
                
        except Exception as e:
            logger.error(f"Error guardando token: {e}")
    
    def build_email_with_actions(self, cuerpo, notification_id, token):
        """Construye el email con botones de acción"""
        action_buttons = f"""
        <div style="margin: 30px 0; text-align: center; border-top: 1px solid #eee; padding-top: 20px;">
            <p style="color: #666; margin-bottom: 15px; font-size: 14px;">Utilizar botones en la Red de Masa o vía VPN</p>
            <table cellpadding="0" cellspacing="0" style="margin: 0 auto;">
                <tr>
                    <td style="padding: 0 8px;">
                        <a href="{self.base_url}/notifications/{notification_id}/received?token={token}" 
                           style="background-color: #28a745; color: white; padding: 10px 16px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold; font-size: 13px;">
                            ✅ Recibido
                        </a>
                    </td>
                    <td style="padding: 0 8px;">
                        <a href="{self.base_url}/notifications/{notification_id}/resolved?token={token}" 
                           style="background-color: #007bff; color: white; padding: 10px 16px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold; font-size: 13px;">
                            ✅ Resuelto
                        </a>
                    </td>
                    <td style="padding: 0 8px;">
                        <a href="{self.base_url}/notifications/{notification_id}/cancel?token={token}" 
                           style="background-color: #dc3545; color: white; padding: 10px 16px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold; font-size: 13px;">
                            ❌ Cancelar
                        </a>
                    </td>
                </tr>
            </table>
            <p style="color: #999; font-size: 12px; margin-top: 15px;">
                Los enlaces expiran en 7 días desde el envío de este email.<br>
                <strong>Nota:</strong> Al marcar como Resuelto o Cancelar, se actualizarán automáticamente todas las notificaciones pendientes relacionadas.
            </p>
        </div>
        """
        
        # Si el cuerpo ya tiene HTML, insertamos antes del cierre
        if '</body>' in cuerpo.lower():
            return cuerpo.replace('</body>', action_buttons + '</body>')
        elif '</html>' in cuerpo.lower():
            return cuerpo.replace('</html>', action_buttons + '</html>')
        else:
            # Si es texto plano o HTML simple, agregamos al final
            return cuerpo + action_buttons
