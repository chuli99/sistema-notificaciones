import pywhatkit, os
from dotenv import load_dotenv
load_dotenv()
numero = os.getenv("WHATSAPP_PHONE_NUMBER")  # Número de teléfono al que se enviarán los mensajes

msg = "Este es un mensaje de prueba enviado desde el servicio de WhatsApp."

pywhatkit.sendwhatmsg_instantly(numero, msg, wait_time=15, tab_close=True)

