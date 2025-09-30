-- Script para agregar el campo IdAlerta a la tabla Notificaciones
-- Ejecutar en SQL Server Management Studio

-- Verificar si la columna IdAlerta ya existe
IF NOT EXISTS (
    SELECT 1 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'Notificaciones' 
    AND COLUMN_NAME = 'IdAlerta'
)
BEGIN
    -- Agregar la columna IdAlerta
    ALTER TABLE Notificaciones 
    ADD IdAlerta NVARCHAR(50) NULL;
    
    PRINT 'Columna IdAlerta agregada correctamente a la tabla Notificaciones';
END
ELSE
BEGIN
    PRINT 'La columna IdAlerta ya existe en la tabla Notificaciones';
END

-- Crear índice para mejorar performance en consultas por IdAlerta
IF NOT EXISTS (
    SELECT 1 
    FROM sys.indexes 
    WHERE name = 'IX_Notificaciones_IdAlerta' 
    AND object_id = OBJECT_ID('Notificaciones')
)
BEGIN
    CREATE INDEX IX_Notificaciones_IdAlerta ON Notificaciones(IdAlerta);
    PRINT 'Índice IX_Notificaciones_IdAlerta creado correctamente';
END
ELSE
BEGIN
    PRINT 'El índice IX_Notificaciones_IdAlerta ya existe';
END

-- Verificar la estructura actualizada
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'Notificaciones' 
  AND COLUMN_NAME IN ('IdNotificacion', 'IdAlerta', 'Source_IdNotificacion', 'Estado')
ORDER BY ORDINAL_POSITION;

-- Consulta de ejemplo para ver notificaciones agrupadas por IdAlerta
SELECT 
    IdAlerta,
    COUNT(*) as TotalNotificaciones,
    COUNT(CASE WHEN Estado = 'pendiente' THEN 1 END) as Pendientes,
    COUNT(CASE WHEN Estado = 'enviado' THEN 1 END) as Enviadas,
    COUNT(CASE WHEN Estado = 'resuelto' THEN 1 END) as Resueltas,
    COUNT(CASE WHEN Estado = 'cancelado' THEN 1 END) as Canceladas
FROM Notificaciones
WHERE IdAlerta IS NOT NULL
GROUP BY IdAlerta
ORDER BY TotalNotificaciones DESC;

PRINT 'Script ejecutado correctamente';
PRINT 'La tabla Notificaciones ahora soporta agrupación por IdAlerta para cascadas';