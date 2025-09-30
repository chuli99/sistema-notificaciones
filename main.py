from app.services.alertas_service import ProcesadorNotificaciones
from app.web.dashboard_plotly import get_app
import time
import logging
import threading
import socket
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_local_ip():
    """Obtiene la IP local de la máquina"""
    try:
        # Crea un socket temporal para obtener la IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def start_dashboard():
    """Inicia el dashboard de Plotly en un hilo separado"""
    host = os.getenv('DASHBOARD_HOST', '0.0.0.0')  # Para que sea accesible desde la red
    port = int(os.getenv('DASHBOARD_PORT', '8050'))
    local_ip = get_local_ip()
    
    logger.info("=" * 60)
    logger.info("🚀 DASHBOARD DE NOTIFICACIONES INICIADO")
    logger.info("=" * 60)
    logger.info(f"📍 Accede al dashboard en:")
    logger.info(f"   🏠 Local:    http://127.0.0.1:{port}")
    logger.info(f"   🌐 Red:      http://{local_ip}:{port}")
    logger.info("=" * 60)
    
    try:
        dash_app = get_app()
        dash_app.run(host=host, port=port, debug=False)
    except Exception as e:
        logger.error(f"❌ Error al iniciar dashboard: {e}")

if __name__ == "__main__":
    logger.info("Iniciando Sistema de Notificaciones...")
    
    # Iniciar dashboard en un hilo separado
    dashboard_thread = threading.Thread(target=start_dashboard, daemon=True)
    dashboard_thread.start()
    
    # Esperar un momento para que el dashboard se inicie
    time.sleep(2)
    
    logger.info("Iniciando procesador de notificaciones...")
    ciclo = 0
    
    try:
        while True:
            try:
                
                start_time = time.time()
                logger.info("🔍 Iniciando procesamiento de notificaciones...")
                
                ProcesadorNotificaciones.procesar_pendientes()
                
                end_time = time.time()
                logger.info(f"✅ Ciclo completado en {end_time - start_time:.2f} segundos")
                
            except Exception as e:
                logger.error(f"❌ Error en ciclo: {e}")
                logger.info("⚠️ Continuando con el siguiente ciclo...")
            
            logger.info("⏳ Esperando 60 segundos para el siguiente ciclo...")
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("🔴 Sistema detenido por el usuario (Ctrl+C)")
    except Exception as e:
        logger.error(f"💥 Error crítico en el bucle principal: {e}")
    finally:
        logger.info("🏁 Sistema de notificaciones finalizado")