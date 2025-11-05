"""
Test para verificar qué registros trae la query de notificaciones pendientes
filtradas por medio='email'
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.utils.database_config import db_config
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_query_notificaciones_email():
    """
    Ejecuta la query del alertas_service para ver qué notificaciones 
    con Medio='email' están pendientes
    """
    
    query = """
    SELECT 
        n.IdNotificacion,
        n.IdTipoNotificacion,
        n.Asunto,
        n.Cuerpo,
        n.Destinatario,
        n.Estado,
        n.Fecha_Envio,
        n.Fecha_Programada,
        n.Medio,
        nt.descripcion as tipo_descripcion,
        nt.destinatarios as destinatarios_default,
        nt.asunto as asunto_default,
        nt.cuerpo as cuerpo_default
    FROM Notificaciones n
    LEFT JOIN Notificaciones_Tipo nt ON n.IdTipoNotificacion = nt.IdTipoNotificacion
    WHERE (n.Fecha_Programada IS NULL OR CAST(n.Fecha_Programada AS DATE) <= CAST(GETDATE() AS DATE))
      AND n.Estado = 'pendiente'
      AND (n.Medio = 'Email' OR n.Medio IS NULL)
    ORDER BY 
        CASE WHEN n.Fecha_Programada IS NULL THEN 0 ELSE 1 END,
        n.Fecha_Programada ASC,
        n.IdNotificacion ASC
    """
    
    try:
        logger.info("=" * 80)
        logger.info("🔍 EJECUTANDO QUERY DE NOTIFICACIONES PENDIENTES (MEDIO=EMAIL)")
        logger.info("=" * 80)
        
        resultados = db_config.execute_query(query)
        
        if not resultados:
            logger.info("❌ No se encontraron notificaciones pendientes con Medio='email'")
            logger.info("\n📊 VERIFICANDO TODAS LAS NOTIFICACIONES EN LA BASE DE DATOS...\n")
            
            # Query para ver todas las notificaciones y sus medios
            query_all = """
            SELECT 
                IdNotificacion,
                Estado,
                Medio,
                Fecha_Programada,
                Asunto
            FROM Notificaciones
            ORDER BY IdNotificacion DESC
            """
            
            todas = db_config.execute_query(query_all)
            
            if todas:
                logger.info(f"📋 Total de notificaciones en BD: {len(todas)}\n")
                
                # Agrupar por estado y medio
                por_estado = {}
                por_medio = {}
                
                for n in todas:
                    estado = n['Estado']
                    medio = n['Medio'] or 'NULL'
                    
                    por_estado[estado] = por_estado.get(estado, 0) + 1
                    por_medio[medio] = por_medio.get(medio, 0) + 1
                
                logger.info("📊 DISTRIBUCIÓN POR ESTADO:")
                for estado, count in por_estado.items():
                    logger.info(f"   - {estado}: {count}")
                
                logger.info("\n📊 DISTRIBUCIÓN POR MEDIO:")
                for medio, count in por_medio.items():
                    logger.info(f"   - {medio}: {count}")
                
                logger.info("\n📋 ÚLTIMAS 10 NOTIFICACIONES:")
                logger.info("-" * 120)
                logger.info(f"{'ID':<6} {'Estado':<12} {'Medio':<12} {'Fecha Programada':<20} {'Asunto':<50}")
                logger.info("-" * 120)
                
                for n in todas[:10]:
                    id_notif = n['IdNotificacion']
                    estado = n['Estado']
                    medio = n['Medio'] or 'NULL'
                    fecha = str(n['Fecha_Programada'])[:19] if n['Fecha_Programada'] else 'NULL'
                    asunto = (n['Asunto'] or 'Sin asunto')[:47]
                    
                    logger.info(f"{id_notif:<6} {estado:<12} {medio:<12} {fecha:<20} {asunto:<50}")
                
            return []
        
        logger.info(f"✅ Se encontraron {len(resultados)} notificaciones pendientes con Medio='email'\n")
        logger.info("=" * 120)
        logger.info(f"{'ID':<6} {'Tipo':<8} {'Estado':<12} {'Medio':<12} {'Fecha Prog.':<20} {'Asunto':<40}")
        logger.info("=" * 120)
        
        for i, notif in enumerate(resultados, 1):
            id_notif = notif['IdNotificacion']
            tipo = notif['IdTipoNotificacion'] or 'NULL'
            estado = notif['Estado']
            medio = notif['Medio'] or 'NULL'
            fecha_prog = str(notif['Fecha_Programada'])[:19] if notif['Fecha_Programada'] else 'NULL'
            asunto = (notif['Asunto'] or notif['asunto_default'] or 'Sin asunto')[:37]
            
            logger.info(f"{id_notif:<6} {tipo:<8} {estado:<12} {medio:<12} {fecha_prog:<20} {asunto:<40}")
            
            # Mostrar detalles de los primeros 3
            if i <= 3:
                logger.info(f"   └─ Destinatarios: {notif['Destinatario'] or notif['destinatarios_default'] or 'Sin destinatarios'}")
                logger.info(f"   └─ Cuerpo: {(notif['Cuerpo'] or notif['cuerpo_default'] or 'Sin cuerpo')[:80]}...")
                logger.info("")
        
        logger.info("=" * 120)
        logger.info(f"\n✅ RESUMEN: {len(resultados)} notificaciones pendientes listas para enviar por email")
        
        return resultados
        
    except Exception as e:
        logger.error(f"❌ Error ejecutando query: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

if __name__ == "__main__":
    logger.info(f"\n🚀 Iniciando test de query - Fecha actual: {datetime.now()}\n")
    resultados = test_query_notificaciones_email()
    logger.info(f"\n✅ Test completado - {len(resultados)} registros encontrados\n")
