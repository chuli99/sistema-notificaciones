-- Script para agregar estado "resuelto" al sistema
-- Ejecutar en SQL Server Management Studio

-- Verificar si ya existe algún CHECK constraint en la columna Estado
SELECT 
    cc.name AS constraint_name,
    cc.definition
FROM sys.check_constraints cc
INNER JOIN sys.columns c ON cc.parent_column_id = c.column_id
INNER JOIN sys.tables t ON cc.parent_object_id = t.object_id
WHERE t.name = 'Notificaciones' 
  AND c.name = 'Estado';

-- Si existe un CHECK constraint, primero eliminarlo
-- Nota: Reemplaza 'nombre_del_constraint' con el nombre real del constraint si existe
-- ALTER TABLE Notificaciones DROP CONSTRAINT nombre_del_constraint;

-- Agregar nuevo CHECK constraint que incluye 'resuelto'
ALTER TABLE Notificaciones 
ADD CONSTRAINT CHK_Notificaciones_Estado 
CHECK (Estado IN ('pendiente', 'enviado', 'recibido', 'error', 'parcial', 'cancelado', 'resuelto'));

-- Verificar que se aplicó correctamente
SELECT 
    cc.name AS constraint_name,
    cc.definition
FROM sys.check_constraints cc
INNER JOIN sys.columns c ON cc.parent_column_id = c.column_id
INNER JOIN sys.tables t ON cc.parent_object_id = t.object_id
WHERE t.name = 'Notificaciones' 
  AND c.name = 'Estado';

-- Consulta de prueba para ver estados únicos actuales
SELECT DISTINCT Estado, COUNT(*) as Cantidad
FROM Notificaciones
GROUP BY Estado
ORDER BY Estado;

PRINT 'Script ejecutado correctamente - Estado "resuelto" agregado';
PRINT 'Estados válidos: pendiente, enviado, recibido, error, parcial, cancelado, resuelto';