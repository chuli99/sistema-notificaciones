
# Sistema de Notificaciones

Sistema automatizado para el procesamiento y envío de notificaciones por email con dashboard de visualización.

## Características

- **Procesamiento automático** de notificaciones pendientes
- **Envío de emails** con configuración SMTP y botones de acción
- **Dashboard interactivo** con gráficos de tendencias y estados
- **Auditoría completa** de todas las operaciones
- **Botones interactivos** en emails: Recibido, Resuelto (con cascada), Cancelar (con cascada)

## Estructura del Proyecto

```
├── Documentación              # Guardo la documentación del proyecto   
├── main.py                    # Punto de entrada principal
├── alertas_service.py         # Lógica de procesamiento de notificaciones
├── database_config.py         # Configuración y conexión a base de datos
├── email_service.py           # Servicio de envío de emails
├── dashboard_plotly.py        # Dashboard de visualización
└── .env                       # Variables de entorno (crear manualmente)
```

## Instalación

1. **Instalar dependencias**:
```bash
pip install pyodbc plotly pandas numpy dash python-dotenv
```

2. **Configurar variables de entorno** en archivo `.env`:
```env
# Base de datos
DB_HOST=tu_servidor
BD_NAME=tu_base_datos
BD_USER=tu_usuario
BD_PASSWORD=tu_contraseña
DB_DRIVER=ODBC Driver 17 for SQL Server

# Email SMTP
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=tu_contraseña_app
EMAIL_SENDER_NAME=Sistema de Notificaciones
```

## Uso

### Procesamiento de Notificaciones
```bash
python main.py
```
Ejecuta el procesador en bucle continuo, revisando notificaciones pendientes cada 60 segundos.

### Dashboard de Visualización
```bash
python dashboard_plotly.py
```
Genera gráficos de tendencias y distribución de estados de las notificaciones.

## Base de Datos

El sistema requiere las siguientes tablas:

- `Notificaciones` - Almacena las notificaciones a enviar
- `Notificaciones_Tipo` - Define tipos de notificaciones con templates
- `Auditoria` - Registra todas las acciones del sistema

## Estados de Notificaciones

- **pendiente** - Esperando ser procesada
- **enviado** - Enviada exitosamente
- **recibido** - Confirmada como recibida por el usuario
- **resuelto** - Marcada como resuelta por el usuario
- **cancelado** - Cancelada por el usuario
- **error** - Error en el envío

## Funcionalidad de Cascada por IdAlerta

Cuando se usa el botón **"Resuelto"** o **"Cancelar"** en un email, el sistema actualiza automáticamente todas las notificaciones **pendientes** que comparten el mismo `IdAlerta`. Esta funcionalidad permite:

- ✅ Resolución automática de alertas pendientes relacionadas
- ❌ Cancelación automática de alertas pendientes relacionadas  
- 📧 Funciona con los botones existentes (sin agregar nuevos)
- 📊 Auditoría completa de operaciones en cascada
- ⚡ Optimización con índices en base de datos

**Ver**: `doc/Funcionalidad_Cascada_IdAlerta.md` para documentación completa.

## Logs y Monitoreo

El sistema genera logs detallados de todas las operaciones:
- Conexiones a base de datos
- Envío de emails
- Errores y excepciones
- Auditoría de cambios de estado

## Configuración SMTP

Para Gmail, usar:
- Habilitar autenticación de 2 factores
- Generar contraseña de aplicación
