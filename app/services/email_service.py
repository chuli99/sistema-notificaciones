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
            
            # Generar token y fecha de expiración si es necesario
            if notification_id:
                action_token = self.generate_action_token()
                expires_at = datetime.now() + timedelta(days=7)
                
                # Guardar token en base de datos
                self.save_action_token(notification_id, action_token, expires_at)
                
                # Agregar botones al cuerpo del email
                cuerpo = self.build_email_with_actions(cuerpo, notification_id, action_token)
            
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
    
    def save_action_token(self, notification_id, token, expires_at):
        """Guarda el token de acción en la base de datos"""
        try:
            query = """
            UPDATE Notificaciones 
            SET action_token = ?, expires_at = ?
            WHERE IdNotificacion = ?
            """
            db_config.execute_non_query(query, [token, expires_at, notification_id])
            logger.info(f"Token guardado para notificación {notification_id}")
        except Exception as e:
            logger.error(f"Error guardando token: {e}")
    
    def build_email_with_actions(self, cuerpo, notification_id, token):
        """Construye el email con botones de acción"""
        action_buttons = f"""
        <div style="margin: 30px 0; text-align: center; border-top: 1px solid #eee; padding-top: 20px;">
            <p style="color: #666; margin-bottom: 15px; font-size: 14px;">¿Fue útil esta notificación?</p>
            <table cellpadding="0" cellspacing="0" style="margin: 0 auto;">
                <tr>
                    <td style="padding: 0 10px;">
                        <a href="{self.base_url}/notifications/{notification_id}/received?token={token}" 
                           style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold;">
                            ✅ Marcar como Recibido
                        </a>
                    </td>
                    <td style="padding: 0 10px;">
                        <a href="{self.base_url}/notifications/{notification_id}/cancel?token={token}" 
                           style="background-color: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold;">
                            ❌ Anular Envío
                        </a>
                    </td>
                </tr>
            </table>
            <p style="color: #999; font-size: 12px; margin-top: 15px;">
                Este enlace expira en 7 días. Sistema de Notificaciones.
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
