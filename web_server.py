from flask import Flask, request, render_template_string, redirect, url_for

from app.services.notification_actions_service import NotificationActionsService
import logging
import os
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')

# Template HTML para mostrar resultados
RESULT_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Notificaciones - Acción Procesada</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .container {
            background: white;
            max-width: 500px;
            margin: 20px;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
        
        .success .icon { color: #28a745; }
        .error .icon { color: #dc3545; }
        
        .message {
            font-size: 18px;
            margin: 20px 0;
            font-weight: 500;
        }
        
        .success .message { color: #155724; }
        .error .message { color: #721c24; }
        
        .details {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin: 20px 0;
            font-size: 14px;
            color: #6c757d;
        }
        
        .close-info {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
            font-size: 14px;
            color: #6c757d;
        }
        
        .btn {
            display: inline-block;
            padding: 10px 20px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin-top: 20px;
            transition: background-color 0.3s;
        }
        
        .btn:hover {
            background-color: #0056b3;
        }
    </style>
</head>
<body>
    <div class="container {{ result_type }}">
        <div class="icon">
            {% if result_type == 'success' %}
                ✅
            {% else %}
                ❌
            {% endif %}
        </div>
        
        <div class="message">{{ message }}</div>
        
        {% if details %}
        <div class="details">
            <strong>Detalles:</strong><br>
            {{ details }}
        </div>
        {% endif %}
        
        <div class="close-info">
            <p>Puedes cerrar esta ventana de forma segura.</p>
            <small>Sistema de Notificaciones - {{ timestamp }}</small>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Página de inicio"""
    return """
    <h1>Sistema de Notificaciones</h1>
    <p>Servidor activo para procesar acciones de notificaciones por email.</p>
    <p>Este endpoint maneja las acciones de los botones en los emails enviados.</p>
    """

@app.route('/notifications/<int:notification_id>/received')
def mark_received(notification_id):
    """Maneja la acción de marcar como recibido"""
    token = request.args.get('token')
    
    if not token:
        return render_template_string(RESULT_TEMPLATE, 
            result_type='error',
            message='Token de seguridad requerido',
            details='El enlace parece estar incompleto o dañado.',
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ), 400
    
    logger.info(f"Procesando marcado como recibido - ID: {notification_id}")
    
    # Procesar la acción
    result = NotificationActionsService.mark_as_received(notification_id, token)
    
    status_code = 200 if result['success'] else 400
    
    return render_template_string(RESULT_TEMPLATE,
        result_type=result['type'],
        message=result['message'],
        details=f'Notificación ID: {notification_id}' if result['success'] else None,
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ), status_code

@app.route('/notifications/<int:notification_id>/cancel')
def cancel_notification(notification_id):
    """Maneja la acción de cancelar notificación"""
    token = request.args.get('token')
    
    if not token:
        return render_template_string(RESULT_TEMPLATE,
            result_type='error', 
            message='Token de seguridad requerido',
            details='El enlace parece estar incompleto o dañado.',
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ), 400
    
    logger.info(f"Procesando cancelación - ID: {notification_id}")
    
    # Procesar la acción
    result = NotificationActionsService.cancel_notification(notification_id, token)
    
    status_code = 200 if result['success'] else 400
    
    return render_template_string(RESULT_TEMPLATE,
        result_type=result['type'],
        message=result['message'], 
        details=f'Notificación ID: {notification_id}' if result['success'] else None,
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ), status_code

@app.route('/notifications/<int:notification_id>/status')
def get_status(notification_id):
    """Obtiene el estado de una notificación (para debugging)"""
    status = NotificationActionsService.get_notification_status(notification_id)
    
    if status:
        return {
            'notification_id': notification_id,
            'estado': status['Estado'],
            'marked_received_at': str(status['marked_received_at']) if status['marked_received_at'] else None,
            'cancelled_at': str(status['cancelled_at']) if status['cancelled_at'] else None,
            'expires_at': str(status['expires_at']) if status['expires_at'] else None,
            'subject': status['Asunto'],
            'recipient': status['Destinatario']
        }
    else:
        return {'error': 'Notification not found'}, 404

@app.route('/admin/stats')
def admin_stats():
    """Estadísticas administrativas"""
    stats = NotificationActionsService.get_statistics()
    return {
        'statistics': stats,
        'timestamp': datetime.now().isoformat()
    }

@app.errorhandler(404)
def not_found(error):
    return render_template_string(RESULT_TEMPLATE,
        result_type='error',
        message='Página no encontrada',
        details='La URL solicitada no existe en este servidor.',
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f"Error interno del servidor: {error}")
    return render_template_string(RESULT_TEMPLATE,
        result_type='error',
        message='Error interno del servidor',
        details='Se ha producido un error inesperado. Por favor, contacte al administrador.',
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ), 500

if __name__ == '__main__':
    from datetime import datetime
    
    # Configuración del servidor
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"🚀 Iniciando servidor de notificaciones en {host}:{port}")
    logger.info(f"🔍 Debug mode: {debug}")
    
    app.run(host=host, port=port, debug=debug)