"""
Test para verificar el servicio de WhatsApp y procesamiento de notificaciones
"""
import sys
import os
import logging

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.alertas_service import NotificacionesService, ProcesadorNotificaciones
from app.services.whatsapp_service import WhatsAppService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
                logger.info(f"Cuerpo: {notif['cuerpo'][:100]}...")
                logger.info(f"Destinatario: {notif['destinatario']}")
                logger.info(f"Estado: {notif['estado']}")
                logger.info(f"Medio: {notif['medio']}")
                logger.info(f"Fecha Programada: {notif['fecha_programada']}")
                
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
    
    whatsapp_service = WhatsAppService()
    
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

def test_procesar_whatsapp():
    """
    Test para procesar notificaciones de WhatsApp (sin enviar realmente)
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Procesar notificaciones de WhatsApp")
    logger.info("=" * 80)
    logger.info("⚠️  NOTA: Este test mostrará el proceso pero NO enviará mensajes reales")
    logger.info("=" * 80)
    
    # Solo mostrar qué se procesaría
    notificaciones = NotificacionesService.obtener_notificaciones_whatsapp_pendientes()
    
    if notificaciones:
        logger.info(f"\n📱 Se procesarían {len(notificaciones)} notificaciones:")
        for notif in notificaciones:
            logger.info(f"\n  ID {notif['IdNotificacion']}:")
            logger.info(f"    → Destinatario: {notif['destinatario']}")
            logger.info(f"    → Asunto: {notif['asunto']}")
            
            if 'error' in notif:
                logger.warning(f"    ⚠️ Error: {notif['error']}")
            else:
                logger.info(f"    ✅ Listo para enviar")
    else:
        logger.info("\nℹ️ No hay notificaciones para procesar")

if __name__ == "__main__":
    print("\n" + "🧪 INICIANDO TESTS DE WHATSAPP SERVICE ".center(80, "="))
    
    # Test 1: Obtener notificaciones
    test_obtener_notificaciones_whatsapp()
    
    # Test 2: Validar números
    test_validar_whatsapp_service()
    
    # Test 3: Procesar (sin enviar)
    test_procesar_whatsapp()
    
    print("\n" + "✅ TESTS COMPLETADOS ".center(80, "=") + "\n")
