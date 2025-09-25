-- Script para agregar funcionalidad de botones de acción en emails
-- Ejecutar en SQL Server Management Studio

-- Agregar nuevas columnas a la tabla Notificaciones (mantenemos Estado existente)
ALTER TABLE Notificaciones ADD action_token VARCHAR(255) NULL;         -- Token seguro para acciones (43 chars aprox)
ALTER TABLE Notificaciones ADD marked_received_at DATETIME2(0) NULL;   -- Fecha cuando fue marcada como recibida
ALTER TABLE Notificaciones ADD cancelled_at DATETIME2(0) NULL;         -- Fecha cuando fue cancelada  
ALTER TABLE Notificaciones ADD expires_at DATETIME2(0) NULL;           -- Fecha de expiración del token

-- Crear índices para optimizar las consultas
CREATE INDEX idx_notifications_token ON Notificaciones(action_token);
CREATE INDEX idx_notifications_estado ON Notificaciones(Estado);

-- Verificar cambios
SELECT TOP 10 IdNotificacion, Estado, action_token, expires_at
FROM Notificaciones
ORDER BY IdNotificacion DESC;

PRINT 'Script ejecutado correctamente - Nuevas columnas agregadas'
PRINT 'NOTA: Se mantiene la columna Estado existente (no se agrega status)';