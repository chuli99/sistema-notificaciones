"""
Script para procesar y enviar notificaciones de WhatsApp pendientes
"""
import logging
from app.services.alertas_service import ProcesadorNotificaciones

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    print("\n" + "="*80)
    print("📱 PROCESANDO NOTIFICACIONES DE WHATSAPP".center(80))
    print("="*80 + "\n")
    
    # Procesar todas las notificaciones de WhatsApp pendientes
    ProcesadorNotificaciones.procesar_whatsapp_pendientes()
    
    print("\n" + "="*80)
    print("✅ PROCESO COMPLETADO".center(80))
    print("="*80 + "\n")
