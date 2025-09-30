-- Crear tabla para manejar tokens individuales por destinatario
-- Esto permite que cada destinatario tenga su propio token único

CREATE TABLE NotificacionDestinatarios (
    IdDestinatario INT IDENTITY(1,1) PRIMARY KEY,
    IdNotificacion INT NOT NULL,
    EmailDestinatario NVARCHAR(255) NOT NULL,
    TokenRespuesta NVARCHAR(255) NULL,
    FechaExpiracion DATETIME2(0) NULL,
    FechaRecibido DATETIME2(0) NULL,
    FechaResuelto DATETIME2(0) NULL,
    FechaCancelacion DATETIME2(0) NULL,
    FechaCreacion DATETIME2(0) DEFAULT GETDATE(),
    
    FOREIGN KEY (IdNotificacion) REFERENCES Notificaciones(IdNotificacion),
    UNIQUE(IdNotificacion, EmailDestinatario) -- Evitar duplicados por notificación y email
);

-- Crear índice para mejorar performance en búsquedas por token
CREATE INDEX IX_NotificacionDestinatarios_Token ON NotificacionDestinatarios(TokenRespuesta);
CREATE INDEX IX_NotificacionDestinatarios_Email ON NotificacionDestinatarios(EmailDestinatario);

-- Migrar datos existentes (si los hay)
INSERT INTO NotificacionDestinatarios (IdNotificacion, EmailDestinatario, TokenRespuesta, FechaExpiracion, FechaRecibido, FechaResuelto, FechaCancelacion)
SELECT 
    IdNotificacion,
    Destinatarios, -- Asumiendo que hay un solo destinatario por registro existente
    TokenRespuesta,
    FechaExpiracion,
    FechaRecibido,
    FechaResuelto,
    FechaCancelacion
FROM Notificaciones 
WHERE TokenRespuesta IS NOT NULL AND Destinatarios IS NOT NULL;