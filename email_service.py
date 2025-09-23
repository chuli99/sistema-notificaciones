import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.sender_name = os.getenv('EMAIL_SENDER_NAME', 'Sistema de Notificaciones')

    def enviar_email(self, destinatario, asunto, cuerpo):
        """
        Intenta enviar un email y retorna True si tiene éxito
        """
        if not all([self.smtp_server, self.smtp_user, self.smtp_password]):
            logger.error("Configuración SMTP incompleta en variables de entorno")
            return False

        try:
            logger.info(f"🔍 Conectando SMTP {self.smtp_server}:{self.smtp_port}")
            
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
