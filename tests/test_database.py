import unittest
import os
import logging
import pyodbc
from dotenv import load_dotenv

# Configuración básica del logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

class TestDatabaseConnection(unittest.TestCase):
    """Pruebas directas para conexión a la base de datos sin usar database_config.py"""
    
    def setUp(self):
        """Preparar el entorno para las pruebas"""
        # Cargar variables de entorno
        load_dotenv()
        
        # Verificar que las variables de entorno necesarias estén configuradas
        required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            self.skipTest(f"Faltan variables de entorno: {', '.join(missing_vars)}")
        
        # Crear los atributos directamente de las variables de entorno
        self.server = os.getenv('DB_HOST')
        self.database = os.getenv('DB_NAME')
        self.username = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.driver = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
    
    def get_connection_string(self):
        """Generar cadena de conexión para la base de datos"""
        conn_str = (
            f'DRIVER={{{self.driver}}};'
            f'SERVER={self.server};'
            f'DATABASE={self.database};'
            f'UID={self.username};'
            f'PWD={self.password};'
            f'Connection Timeout=30;'
            f'Login Timeout=30;'
            f'TrustServerCertificate=yes;'
        )
        return conn_str
    
    def test_connection(self):
        """Probar la conexión a la base de datos directamente"""
        conn_str = self.get_connection_string()
        logger.info(f"Intentando conectar a {self.server} con base de datos {self.database}")
        
        try:
            with pyodbc.connect(self.get_connection_string()) as conn:
                cursor = conn.cursor()
                # Intentar hacer una consulta simple
                cursor.execute("SELECT 1 AS test_value")
                
                # Obtener el resultado
                result = cursor.fetchone()
                
                # Verificar que obtuvimos el valor esperado
                self.assertEqual(result.test_value, 1, "No se obtuvo el valor esperado de la consulta")
                
                logger.info("✅ Conexión a base de datos exitosa")
                logger.info(f"Servidor: {self.server}")
                logger.info(f"Base de datos: {self.database}")
                return True
        except Exception as e:
            logger.error(f"❌ Error probando conexión: {e}")
            self.fail(f"La conexión a la base de datos falló: {e}")
            return False
    
    def test_query_tables(self):
        """Intentar consultar las tablas del sistema para verificar permisos"""
        try:
            with pyodbc.connect(self.get_connection_string()) as conn:
                cursor = conn.cursor()
                # Consultar las primeras 5 tablas del sistema
                cursor.execute("""
                    SELECT TOP 5 
                        t.name AS table_name,
                        s.name AS schema_name
                    FROM 
                        sys.tables t
                    INNER JOIN 
                        sys.schemas s ON t.schema_id = s.schema_id
                    ORDER BY 
                        t.name
                """)
                
                tables = cursor.fetchall()
                
                # Verificar que obtuvimos al menos un resultado
                self.assertTrue(len(tables) > 0, "No se encontraron tablas o no se tienen permisos para verlas")
                
                # Mostrar las tablas encontradas
                logger.info(f"✅ Se encontraron {len(tables)} tablas en la base de datos:")
                for table in tables:
                    logger.info(f"  • {table.schema_name}.{table.table_name}")
                    
        except Exception as e:
            logger.error(f"❌ Error consultando tablas: {e}")
            self.fail(f"Error al consultar tablas del sistema: {e}")


if __name__ == '__main__':
    # Si ejecutamos este archivo directamente, ejecutar las pruebas
    print("\n🔍 Ejecutando pruebas de conexión a la base de datos...")
    unittest.main()
