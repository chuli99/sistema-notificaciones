"""
Script de prueba para enviar un mensaje de WhatsApp directamente
⚠️ IMPORTANTE: Asegúrate de tener WhatsApp Web abierto y sesión iniciada
"""
import logging
from app.services.whatsapp_service import WhatsAppService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    print("\n" + "="*80)
    print("📱 TEST DE ENVÍO DE WHATSAPP".center(80))
    print("="*80)
    print("\n⚠️  IMPORTANTE:")
    print("   1. Este script abrirá WhatsApp Web en tu navegador")
    print("   2. Asegúrate de tener WhatsApp Web con sesión iniciada")
    print("   3. El mensaje se enviará automáticamente después de 10 segundos")
    print("\n" + "="*80 + "\n")
    
    # Crear servicio
    whatsapp_service = WhatsAppService()
    
    if not whatsapp_service.disponible:
        print("❌ pywhatkit no está disponible. Instálalo con: pip install pywhatkit")
        exit(1)
    
    # Número de destino (reemplaza con tu número de prueba)
    # IMPORTANTE: Debe incluir código de país con +
    numero_destino = "+573001234567"  # 🔴 CAMBIA ESTE NÚMERO
    
    # Mensaje de prueba
    asunto = "🧪 Mensaje de Prueba"
    cuerpo = "Este es un mensaje de prueba del sistema de notificaciones. Si lo recibes, ¡todo funciona correctamente!"
    
    print(f"📤 Enviando mensaje a: {numero_destino}")
    print(f"📝 Asunto: {asunto}\n")
    
    input("Presiona ENTER para continuar o CTRL+C para cancelar...")
    
    # Enviar mensaje
    resultado = whatsapp_service.enviar_notificacion(
        destinatario=numero_destino,
        asunto=asunto,
        cuerpo=cuerpo
    )
    
    if resultado:
        print("\n✅ Mensaje enviado exitosamente!")
    else:
        print("\n❌ Error al enviar el mensaje. Revisa los logs arriba.")
    
    print("\n" + "="*80 + "\n")
