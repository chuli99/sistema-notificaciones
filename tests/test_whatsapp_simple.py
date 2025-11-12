"""
Test simple para verificar el servicio de WhatsApp sin conflictos de imports
"""
import sys
import os
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cambiar el directorio de trabajo antes de importar
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Agregar el directorio raíz al path
if os.path.dirname(__file__) not in sys.path:
    sys.path.insert(0, os.path.dirname(__file__))

# Ahora importar los servicios
from app.services.alertas_service import NotificacionesService
from app.services.whatsapp_service import WhatsAppService

def test_obtener_notificaciones_whatsapp():
    """
    Test para verificar que la query obtiene notificaciones de WhatsApp correctamente
    """
    logger.info("=" * 80)
    logger.info("TEST: Obtener notificaciones de WhatsApp pendientes")
    logger.info("=" * 80)
    
    try:
        notificaciones = NotificacionesService.obtener_notificaciones_whatsapp_pendientes()
        
        logger.info(f"\n📊 RESULTADOS:")
        logger.info(f"Total de notificaciones encontradas: {len(notificaciones)}")
        
        if notificaciones:
            logger.info("\n📋 DETALLE DE NOTIFICACIONES:")
            for i, notif in enumerate(notificaciones, 1):
                logger.info(f"\n--- Notificación {i} ---")
                logger.info(f"ID: {notif['IdNotificacion']}")
                logger.info(f"Tipo: {notif['tipo_descripcion']}")
                logger.info(f"Asunto: {notif['asunto']}")
                logger.info(f"Destinatario: {notif['destinatario']}")
                logger.info(f"Estado: {notif['estado']}")
                logger.info(f"Medio: {notif['medio']}")
                
                if 'error' in notif:
                    logger.warning(f"⚠️ ERROR: {notif['error']}")
        else:
            logger.info("\nℹ️ No hay notificaciones de WhatsApp pendientes para procesar")
        
        return notificaciones
        
    except Exception as e:
        logger.error(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_validar_whatsapp_service():
    """
    Test para validar el WhatsAppService
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Validación de números de WhatsApp")
    logger.info("=" * 80)
    
    try:
        whatsapp_service = WhatsAppService()
        
        # Verificar si está disponible
        if not whatsapp_service.disponible:
            logger.warning("⚠️ WhatsApp Service no está disponible (pywhatkit no instalado correctamente)")
            return
        
        numeros_test = [
            "+573001234567",  # Válido
            "3001234567",      # Sin código de país
            "+57 300 123 4567",  # Con espacios
            "+57-300-123-4567",  # Con guiones
            "",                # Vacío
            "+123",            # Muy corto
            "+123456789012345678",  # Muy largo
            "+57ABC1234567",   # Con letras
        ]
        
        logger.info("\n📋 VALIDACIÓN DE NÚMEROS:")
        for numero in numeros_test:
            valido, mensaje = whatsapp_service.validar_numero(numero)
            status = "✅ VÁLIDO" if valido else "❌ INVÁLIDO"
            logger.info(f"{status}: '{numero}' → {mensaje}")
    
    except Exception as e:
        logger.error(f"❌ Error en validación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "🧪 INICIANDO TESTS DE WHATSAPP SERVICE ".center(80, "="))
    
    # Test 1: Obtener notificaciones
    test_obtener_notificaciones_whatsapp()
    
    # Test 2: Validar números
    test_validar_whatsapp_service()
    
    print("\n" + "✅ TESTS COMPLETADOS ".center(80, "=") + "\n")
