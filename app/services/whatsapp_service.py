import os
import logging
import sys
from dotenv import load_dotenv

# Solución al conflicto de nombres con carpeta 'app'
# Guardar y remover temporalmente 'app' del sys.modules
_app_backup = sys.modules.pop('app', None)
_app_services_backup = sys.modules.pop('app.services', None)
_app_utils_backup = sys.modules.pop('app.utils', None)

try:
    import pywhatkit
    PYWHATKIT_DISPONIBLE = True
except Exception as e:
    pywhatkit = None
    PYWHATKIT_DISPONIBLE = False
    print(f"Error importando pywhatkit: {e}")

# Restaurar módulos 'app' originales
if _app_backup:
    sys.modules['app'] = _app_backup
if _app_services_backup:
    sys.modules['app.services'] = _app_services_backup
if _app_utils_backup:
    sys.modules['app.utils'] = _app_utils_backup

load_dotenv()
logger = logging.getLogger(__name__)

class WhatsAppService:
    """
    Servicio para enviar notificaciones por WhatsApp usando pywhatkit.
    LIMITACIONES: Solo envía mensajes de texto, sin botones interactivos.
    """
    
    def __init__(self):
        self.numero_default = os.getenv("WHATSAPP_PHONE_NUMBER")
        self.wait_time = int(os.getenv("WHATSAPP_WAIT_TIME", 30))  # Tiempo de espera antes de escribir
        self.close_time = int(os.getenv("WHATSAPP_CLOSE_TIME", 10))  # Tiempo antes de cerrar pestaña
        self.disponible = PYWHATKIT_DISPONIBLE
        
        if not self.disponible:
            logger.debug("pywhatkit no disponible - servicio WhatsApp deshabilitado")
        else:
            logger.debug("WhatsAppService inicializado correctamente")
    
    def validar_numero(self, numero):
        """
        Valida formato básico de número de teléfono.
        Debe incluir código de país con +
        """
        if not numero:
            return False, "Número vacío"
        
        numero = numero.strip()
        
        if not numero.startswith('+'):
            return False, f"Número debe incluir código de país: {numero}"
        
        # Remover caracteres no numéricos excepto el +
        numeros_solo = numero.replace('+', '').replace(' ', '').replace('-', '')
        
        if not numeros_solo.isdigit():
            return False, f"Número contiene caracteres inválidos: {numero}"
        
        if len(numeros_solo) < 10 or len(numeros_solo) > 15:
            return False, f"Longitud de número inválida: {numero}"
        
        return True, numero
    
    def enviar_notificacion(self, destinatario, asunto, cuerpo):
        """
        Envía notificación INFORMATIVA por WhatsApp (sin botones de respuesta).
        Solo para alertas que NO requieren interacción.
        
        Args:
            destinatario: Número de teléfono con código de país (ej: +573001234567)
            asunto: Título del mensaje
            cuerpo: Contenido del mensaje
            
        Returns:
            bool: True si se envió correctamente, False en caso de error
        """
        try:
            # Verificar que pywhatkit esté disponible
            if not self.disponible:
                logger.error("❌ pywhatkit no está disponible")
                return False
            
            # Usar número por defecto si no se proporciona destinatario
            numero = destinatario or self.numero_default
            
            if not numero:
                logger.error("❌ No hay número de destinatario configurado")
                return False
            
            # Validar formato del número
            valido, resultado = self.validar_numero(numero)
            if not valido:
                logger.error(f"❌ Número inválido: {resultado}")
                return False
            
            numero = resultado  # Usar número validado
            
            # Construir mensaje de texto
            mensaje = f"🔔 *{asunto}*\n\n{cuerpo}"
            
            logger.info(f"📱 Enviando WhatsApp a {numero}...")
            logger.info(f"⏱️ Tiempos: wait={self.wait_time}s, close={self.close_time}s")
            
            # Enviar mensaje
            # wait_time: tiempo para que cargue WhatsApp Web antes de escribir
            # close_time: tiempo antes de cerrar pestaña (para que se envíe el mensaje)
            pywhatkit.sendwhatmsg_instantly(
                phone_no=numero,
                message=mensaje,
                wait_time=self.wait_time,
                tab_close=True,
                close_time=self.close_time
            )
            
            logger.info(f"✅ WhatsApp enviado exitosamente a {numero}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando WhatsApp a {destinatario}: {type(e).__name__} - {str(e)}")
            return False

