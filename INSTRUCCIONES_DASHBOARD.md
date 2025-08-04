mai # 🔔 Dashboard de Notificaciones - Manual de Uso

## 🚀 Cómo ejecutar el Dashboard

### 1. Ejecutar el Sistema Completo (Recomendado)
```bash
python main.py
```

### 2. Ejecutar Solo el Dashboard Interactivo
```bash
python dashboard_plotly.py
```

**El dashboard estará disponible en: http://localhost:8050**

### 3. Configuración de Puerto (Opcional)
Crear un archivo `.env` con:
```
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8050
```

## ⚠️ Solución de Problemas Comunes

### Error: "app.run_server has been replaced by app.run"
**✅ Solucionado**: El código ahora usa `app.run()` que es compatible con las versiones más recientes de Dash.

### Error: "El nombre de columna 'Fecha_Creacion' no es válido"
**✅ Solucionado**: El código ahora usa solo las columnas que existen en tu tabla SQL Server:
- ✅ `IdTipoNotificacion`
- ✅ `Asunto` 
- ✅ `Cuerpo`
- ✅ `Destinatario`
- ✅ `Estado` (se establece como 'pendiente')
- ✅ `Fecha_Envio` se completa automáticamente por SQL Server

### Dashboard no carga en 127.0.0.1:8050
1. **Verifica** que no haya errores en la consola
2. **Espera** 2-3 segundos después del mensaje de inicio
3. **Refresca** la página del navegador
4. **Intenta** ejecutar solo el dashboard: `python dashboard_plotly.py`

### ✅ Verificación Rápida del Sistema
Para verificar que todo funciona correctamente:
```bash
# 1. Prueba el sistema completo
python test_dashboard.py

# 2. Prueba específica de callbacks (si hay errores _dash-update-component)
python test_callbacks.py

# 3. Si todo está bien, ejecuta el dashboard
python main.py
```

### Error: "Exception on /_dash-update-component [POST]"
**✅ Solucionado**: Los callbacks han sido simplificados y mejorados. Si persiste:
1. Ejecuta `python test_callbacks.py` para diagnóstico específico
2. Revisa los logs de la consola para detalles del error
3. Asegúrate de que la base de datos tenga datos de tipos de notificación

## 📝 Crear Nuevas Notificaciones

### ✅ Funcionalidades Disponibles

1. **Selector de Tipo de Notificación** (Obligatorio)
   - Lista desplegable con todos los tipos disponibles
   - Cada tipo tiene configuraciones por defecto

2. **Campos Opcionales**:
   - **Asunto**: Si no se completa, usa el asunto por defecto del tipo
   - **Cuerpo**: Acepta HTML básico, si no se completa usa el cuerpo por defecto
   - **Destinatarios Adicionales**: Se suman a los destinatarios por defecto del tipo
   - **📅 Fecha Programada**: Permite programar el envío para una fecha específica

3. **Botón Crear Notificación**
   - Valida los datos y fechas
   - Crea la notificación con estado "pendiente"
   - Programa el envío según la fecha seleccionada
   - Muestra mensajes de éxito o error

### 🔄 Flujo de Trabajo

1. **Selecciona** un tipo de notificación de la lista
2. **Personaliza** (opcional) el contenido:
   - Asunto específico
   - Cuerpo del mensaje (con HTML si quieres)
   - Destinatarios adicionales
   - 📅 Fecha programada para el envío
3. **Haz clic** en "📧 Crear Notificación"
4. **Verifica** el mensaje de confirmación
5. **La notificación se procesa** según la fecha programada o inmediatamente si no se especifica fecha

### 📧 Manejo de Destinatarios

- **Destinatarios del Tipo**: Se toman automáticamente del tipo seleccionado
- **Destinatarios Adicionales**: Se pueden agregar emails separados por comas o punto y coma
- **Resultado Final**: Se combinan ambos, eliminando duplicados

#### 🔄 **Separadores Soportados**

El sistema soporta **múltiples formatos** para separar destinatarios:

1. **Comas (`,`)** - Formato estándar:
   ```
   usuario1@ejemplo.com, usuario2@ejemplo.com, admin@empresa.com
   ```

2. **Punto y coma (`;`)** - Formato alternativo:
   ```
   usuario1@ejemplo.com; usuario2@ejemplo.com; admin@empresa.com
   ```

### 📅 Programación de Envíos

#### ✅ **Funcionamiento**

- **Sin fecha programada**: La notificación se envía inmediatamente (estado pendiente)
- **Con fecha programada**: La notificación se envía solo cuando llegue la fecha especificada
- **Validaciones**: No permite fechas pasadas, solo futuras o el día actual

#### 🔄 **Lógica de Procesamiento**

El sistema verifica en este orden:
1. **¿Es la fecha programada?** → Solo procesa si `Fecha_Programada <= AHORA` o es `NULL`
2. **¿Está pendiente?** → Solo procesa notificaciones con estado `'pendiente'`
3. **¿Tiene destinatarios válidos?** → Combina destinatarios individuales + del tipo

#### 📋 **Ejemplos de Uso**

**Notificación Inmediata:**
- Fecha Programada: (vacía)
- Resultado: Se envía en el siguiente ciclo de procesamiento

**Notificación Programada:**
- Fecha Programada: 15/08/2024
- Resultado: Se envía solo el 15/08/2024 o después

**Notificación Vencida:**
- Fecha Programada: 10/08/2024 (y hoy es 12/08/2024)  
- Resultado: Se envía inmediatamente en el siguiente procesamiento

### 🎨 Formato HTML en el Cuerpo

Puedes usar etiquetas HTML básicas:
```html
<b>Texto en negrita</b>
<i>Texto en cursiva</i>
<br>Salto de línea
<p>Párrafo</p>
<a href="url">Enlace</a>
```

## 📊 Análisis de Notificaciones

### Gráficos Disponibles

1. **Gráfico de Líneas**:
   - Tendencia temporal de notificaciones
   - Filtrable por período (1 semana, 1 mes, 3 meses)
   - Agrupado por tipo de notificación

2. **Gráfico de Dona**:
   - Distribución de estados (pendiente, enviado, error)
   - Datos del último mes

### 🔄 Actualización Automática

- Los gráficos se actualizan automáticamente al cambiar el período
- Para ver las nuevas notificaciones creadas, refresca la página

## ⚙️ Estados de Notificación

- **pendiente**: Recién creada, esperando procesamiento
- **enviado**: Enviada exitosamente a todos los destinatarios
- **parcial**: Enviada a algunos destinatarios, con errores en otros
- **error**: No se pudo enviar a ningún destinatario

## 🔧 Troubleshooting

### Error: "Debe seleccionar un tipo de notificación"
- **Solución**: Es obligatorio seleccionar un tipo antes de crear

### Error en la creación
- **Verifica**: Conexión a la base de datos
- **Revisa**: Logs en la consola del servidor
- **Confirma**: Que existan tipos de notificación en la BD

### Dashboard no carga
- **Verifica**: Que las dependencias estén instaladas (`pip install -r requirements.txt`)
- **Confirma**: Que la base de datos esté disponible
- **Revisa**: Los logs de error en la consola

## 🎯 Tips de Uso

1. **Usa tipos por defecto**: Para notificaciones estándar, solo selecciona el tipo
2. **Personaliza cuando necesites**: Agrega contenido específico solo cuando sea necesario
3. **Múltiples destinatarios**: Separa emails con comas en el campo adicional
4. **Monitorea el dashboard**: Usa los gráficos para analizar tendencias

¡El sistema procesará automáticamente las notificaciones creadas! 🚀
