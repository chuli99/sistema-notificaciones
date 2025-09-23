import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database_config import db_config
import logging
import dash
from dash import dcc, html, Input, Output, callback, State
from dash.exceptions import PreventUpdate
import os
from dotenv import load_dotenv
import warnings

# Suprimir warning específico de deprecación de pandas/plotly
warnings.filterwarnings('ignore', category=FutureWarning, module='_plotly_utils.basevalidators')

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

class DashboardNotificacionesPlotly:
    def __init__(self):
        self.periodo_actual = '1_mes'
        self.datos_cache = {}
    
    def obtener_tipos_notificacion(self):
        """
        Obtiene los tipos de notificación disponibles
        """
        query = """
        SELECT IdTipoNotificacion, descripcion 
        FROM Notificaciones_Tipo 
        ORDER BY descripcion
        """
        try:
            resultados = db_config.execute_query(query)
            return resultados
        except Exception as e:
            logger.error(f"Error al obtener tipos de notificación: {e}")
            return []
    
    def crear_notificacion(self, tipo_id, asunto, cuerpo, destinatarios, fecha_programada=None):
        """
        Crea una nueva notificación
        """
        query = """
        INSERT INTO Notificaciones (IdTipoNotificacion, Asunto, Cuerpo, Destinatario, Estado, Fecha_Programada)
        VALUES (?, ?, ?, ?, 'pendiente', ?)
        """
        try:
            params = [
                tipo_id if tipo_id else None,
                asunto if asunto.strip() else None,
                cuerpo if cuerpo.strip() else None,
                destinatarios if destinatarios.strip() else None,
                fecha_programada if fecha_programada else None
            ]
            
            db_config.execute_non_query(query, params)
            
            fecha_info = f" programada para {fecha_programada.strftime('%d/%m/%Y')}" if fecha_programada else " inmediata"
            logger.info(f"Notificación creada - Tipo: {tipo_id}{fecha_info}")
            return True, "Notificación creada exitosamente"
        except Exception as e:
            logger.error(f"Error al crear notificación: {e}")
            return False, f"Error al crear la notificación: {str(e)}"
        
    def obtener_datos_por_periodo(self, periodo='1_mes'):
        """
        Se obtiene datos de notificaciones por período para el gráfico de líneas
        """
        if periodo in self.datos_cache:
            return self.datos_cache[periodo]
            
        fecha_fin = datetime.now()
        if periodo == '1_semana':
            fecha_inicio = fecha_fin - timedelta(days=7)
            titulo_periodo = "Última Semana"
        elif periodo == '1_mes':
            fecha_inicio = fecha_fin - timedelta(days=30)
            titulo_periodo = "Último Mes"
        elif periodo == '3_meses':
            fecha_inicio = fecha_fin - timedelta(days=90)
            titulo_periodo = "Últimos 3 Meses"
        else:
            raise ValueError("Período no válido")
        
        query = """
        SELECT 
            nt.IdTipoNotificacion,
            nt.descripcion as TipoDescripcion,
            CAST(n.Fecha_Envio AS DATE) as Fecha,
            COUNT(n.IdNotificacion) as Cantidad,
            COUNT(CASE WHEN n.Estado = 'enviado' THEN 1 END) as CantidadEnviadas,
            COUNT(CASE WHEN n.Estado = 'error' THEN 1 END) as CantidadError,
            COUNT(CASE WHEN n.Estado = 'pendiente' THEN 1 END) as CantidadPendientes
        FROM Notificaciones n
        INNER JOIN Notificaciones_Tipo nt ON n.IdTipoNotificacion = nt.IdTipoNotificacion
        WHERE n.Fecha_Envio >= ? AND n.Fecha_Envio <= ?
        GROUP BY nt.IdTipoNotificacion, nt.descripcion, CAST(n.Fecha_Envio AS DATE)
        ORDER BY Fecha ASC, nt.descripcion
        """
        
        try:
            resultados = db_config.execute_query(query, [fecha_inicio, fecha_fin])
            datos = {
                'resultados': resultados,
                'titulo_periodo': titulo_periodo,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin
            }
            self.datos_cache[periodo] = datos
            return datos
        except Exception as e:
            logger.error(f"Error al obtener datos por período: {e}")
            return {'resultados': [], 'titulo_periodo': titulo_periodo}
    
    def obtener_datos_estados(self):
        """
        Se obtiene datos para el gráfico de dona (distribución de estados)
        """
        query = """
        SELECT 
            n.Estado,
            COUNT(n.IdNotificacion) as Cantidad
        FROM Notificaciones n
        WHERE n.Fecha_Envio >= DATEADD(month, -1, GETDATE())
        GROUP BY n.Estado
        ORDER BY Cantidad DESC
        """
        
        try:
            resultados = db_config.execute_query(query)
            return resultados
        except Exception as e:
            logger.error(f"Error al obtener datos de estados: {e}")
            return []
    
    def crear_grafico_lineas(self, periodo='1_mes'):
        """
        Crea el gráfico de líneas con tendencia temporal usando Plotly
        """
        datos = self.obtener_datos_por_periodo(periodo)
        
        if not datos['resultados']:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos para mostrar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            fig.update_layout(
                title=f'Tendencia de Notificaciones - {datos["titulo_periodo"]}',
                xaxis_title="Fecha",
                yaxis_title="Cantidad de Notificaciones"
            )
            return fig
        
        # Convertir a DataFrame
        df = pd.DataFrame(datos['resultados'])
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        
        # Convertir fechas a formato numpy array para evitar warning de deprecación
        df['Fecha'] = np.array(df['Fecha'].dt.to_pydatetime())
        
        # Crear figura
        fig = go.Figure()
        
        # Obtener tipos únicos y colores
        tipos_unicos = df['TipoDescripcion'].unique()
        colores = px.colors.qualitative.Set3[:len(tipos_unicos)]
        
        # Crear líneas para cada tipo
        for i, tipo in enumerate(tipos_unicos):
            datos_tipo = df[df['TipoDescripcion'] == tipo]
            fig.add_trace(go.Scatter(
                x=datos_tipo['Fecha'],
                y=datos_tipo['Cantidad'],
                mode='lines+markers',
                name=tipo,
                line=dict(width=3, color=colores[i]),
                marker=dict(size=8),
                hovertemplate='<b>%{fullData.name}</b><br>' +
                            'Fecha: %{x}<br>' +
                            'Cantidad: %{y}<br>' +
                            '<extra></extra>'
            ))
        
        # Añadir línea de tendencia general si hay suficientes datos
        if len(df) > 3:
            df_agrupado = df.groupby('Fecha')['Cantidad'].sum().reset_index()
            if len(df_agrupado) > 1:
                # Calcular tendencia
                x_num = np.arange(len(df_agrupado))
                z = np.polyfit(x_num, df_agrupado['Cantidad'], 1)
                tendencia = np.poly1d(z)(x_num)
                
                fig.add_trace(go.Scatter(
                    x=df_agrupado['Fecha'],
                    y=tendencia,
                    mode='lines',
                    name='Tendencia General',
                    line=dict(dash='dash', width=2, color='red'),
                    opacity=0.7,
                    hovertemplate='<b>Tendencia General</b><br>' +
                                'Fecha: %{x}<br>' +
                                'Valor: %{y:.1f}<br>' +
                                '<extra></extra>'
                ))
        
        # Configurar layout
        fig.update_layout(
            title={
                'text': f'Tendencia de Notificaciones - {datos["titulo_periodo"]}',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            xaxis_title="Fecha",
            yaxis_title="Cantidad de Notificaciones",
            hovermode='x unified',
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            ),
            template='plotly_white',
            height=500
        )
        
        return fig
    
    def crear_grafico_dona(self):
        """
        Crea el gráfico de dona para mostrar distribución de estados usando Plotly
        """
        datos_estados = self.obtener_datos_estados()
        
        if not datos_estados:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos para mostrar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            fig.update_layout(title="Distribución de Estados<br>(Último Mes)")
            return fig
        
        # Preparar datos
        estados = [item['Estado'] for item in datos_estados]
        cantidades = [item['Cantidad'] for item in datos_estados]
        
        # Colores personalizados para cada estado
        colores_estados = {
            'enviado': '#2ecc71',    # Verde
            'pendiente': '#f39c12',  # Naranja
            'error': '#e74c3c'       # Rojo
        }
        
        colores = [colores_estados.get(estado.lower(), '#95a5a6') for estado in estados]
        
        # Crear gráfico de dona
        fig = go.Figure(data=[go.Pie(
            labels=estados,
            values=cantidades,
            hole=0.5,
            marker_colors=colores,
            textinfo='label+percent',
            textposition='outside',
            hovertemplate='<b>%{label}</b><br>' +
                         'Cantidad: %{value}<br>' +
                         'Porcentaje: %{percent}<br>' +
                         '<extra></extra>'
        )])
        
        # Añadir texto central
        total = sum(cantidades)
        fig.add_annotation(
            text=f"Total<br>{total}",
            x=0.5, y=0.5,
            font_size=16,
            font_color="black",
            showarrow=False
        )
        
        # Configurar layout
        fig.update_layout(
            title={
                'text': 'Distribución de Estados<br>(Último Mes)',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16}
            },
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.02
            ),
            height=500,
            template='plotly_white'
        )
        
        return fig
    
    def crear_dashboard_estatico(self, periodo='1_mes'):
        """
        Crea un dashboard estático con subplots
        """
        # Crear subplots
        fig = make_subplots(
            rows=1, cols=2,
            column_widths=[0.7, 0.3],
            specs=[[{"secondary_y": False}, {"type": "domain"}]],
            subplot_titles=('Tendencia de Notificaciones', 'Distribución de Estados')
        )
        
        # Obtener datos para gráfico de líneas
        datos = self.obtener_datos_por_periodo(periodo)
        if datos['resultados']:
            df = pd.DataFrame(datos['resultados'])
            df['Fecha'] = pd.to_datetime(df['Fecha'])
            
            # Convertir fechas a formato numpy array para evitar warning de deprecación
            df['Fecha'] = np.array(df['Fecha'].dt.to_pydatetime())
            
            tipos_unicos = df['TipoDescripcion'].unique()
            colores = px.colors.qualitative.Set3[:len(tipos_unicos)]
            
            for i, tipo in enumerate(tipos_unicos):
                datos_tipo = df[df['TipoDescripcion'] == tipo]
                fig.add_trace(
                    go.Scatter(
                        x=datos_tipo['Fecha'],
                        y=datos_tipo['Cantidad'],
                        mode='lines+markers',
                        name=tipo,
                        line=dict(width=3, color=colores[i]),
                        marker=dict(size=6)
                    ),
                    row=1, col=1
                )
        
        # Obtener datos para gráfico de dona
        datos_estados = self.obtener_datos_estados()
        if datos_estados:
            estados = [item['Estado'] for item in datos_estados]
            cantidades = [item['Cantidad'] for item in datos_estados]
            
            colores_estados = {
                'enviado': '#2ecc71',
                'pendiente': '#f39c12',
                'error': '#e74c3c'
            }
            colores = [colores_estados.get(estado.lower(), '#95a5a6') for estado in estados]
            
            fig.add_trace(
                go.Pie(
                    labels=estados,
                    values=cantidades,
                    hole=0.4,
                    marker_colors=colores,
                    textinfo='label+percent'
                ),
                row=1, col=2
            )
        
        # Configurar layout
        fig.update_layout(
            title={
                'text': 'Dashboard de Notificaciones del Sistema',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 24}
            },
            height=600,
            template='plotly_white',
            showlegend=True
        )
        
        # Configurar ejes
        fig.update_xaxes(title_text="Fecha", row=1, col=1)
        fig.update_yaxes(title_text="Cantidad de Notificaciones", row=1, col=1)
        
        return fig

def crear_dashboard_dash():
    """
    Crea una aplicación Dash interactiva
    """
    app = dash.Dash(__name__)
    dashboard = DashboardNotificacionesPlotly()
    
    # Obtener tipos de notificación para el dropdown
    tipos = dashboard.obtener_tipos_notificacion()
    opciones_tipos = [{'label': tipo['descripcion'], 'value': tipo['IdTipoNotificacion']} for tipo in tipos]
    
    app.layout = html.Div([
        html.H1("Dashboard de Notificaciones del Sistema", 
                style={'textAlign': 'center', 'marginBottom': 30}),
        
        # Sección de creación de notificaciones
        html.Div([
            html.H3("🔔 Crear Nueva Notificación", 
                   style={'color': '#2c3e50', 'borderBottom': '2px solid #3498db', 'paddingBottom': '10px'}),
            
            html.Div([
                html.Div([
                    html.Label("Tipo de Notificación:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                    dcc.Dropdown(
                        id='tipo-notificacion-dropdown',
                        options=opciones_tipos,
                        placeholder="Seleccione un tipo de notificación...",
                        style={'marginBottom': '15px'}
                    ),
                    
                    html.Label("Asunto (Opcional):", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                    dcc.Input(
                        id='asunto-input',
                        type='text',
                        placeholder='Deje vacío para usar el asunto por defecto del tipo',
                        style={'width': '100%', 'marginBottom': '15px', 'padding': '8px'}
                    ),
                    
                    html.Label("Destinatarios Adicionales (Opcional):", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                    dcc.Input(
                        id='destinatarios-input',
                        type='email',
                        placeholder='email1@ejemplo.com; email2@ejemplo.com (use ; o , como separador)',
                        style={'width': '100%', 'marginBottom': '15px', 'padding': '8px'}
                    ),
                    
                    html.Label("Fecha Programada:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                    dcc.DatePickerSingle(
                        id='fecha-programada-picker',
                        placeholder='Seleccionar fecha de envío',
                        display_format='DD/MM/YYYY',
                        style={'width': '100%', 'marginBottom': '15px'}
                    ),
                    html.Small("Si no selecciona fecha, se enviará inmediatamente. Las notificaciones se procesan a partir del día seleccionado (cualquier hora).", 
                              style={'color': '#666', 'fontSize': '12px', 'display': 'block', 'marginBottom': '15px'}),
                ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
                
                html.Div([
                    html.Label("Cuerpo del Mensaje (Opcional):", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                    dcc.Textarea(
                        id='cuerpo-textarea',
                        placeholder='Deje vacío para usar el cuerpo por defecto del tipo. Puede usar HTML básico.',
                        style={'width': '100%', 'height': '120px', 'marginBottom': '15px', 'padding': '8px'}
                    ),
                    
                    html.Button(
                        '📧 Crear Notificación', 
                        id='crear-notificacion-btn',
                        style={
                            'backgroundColor': '#27ae60', 
                            'color': 'white', 
                            'border': 'none',
                            'padding': '12px 24px',
                            'fontSize': '16px',
                            'borderRadius': '5px',
                            'cursor': 'pointer',
                            'width': '100%'
                        }
                    ),
                ], style={'width': '48%', 'display': 'inline-block', 'marginLeft': '4%', 'verticalAlign': 'top'}),
            ]),
            
            # Div para mostrar mensajes de resultado
            html.Div(id='mensaje-resultado', style={'marginTop': '15px'}),
            
        ], style={
            'margin': '20px', 
            'padding': '20px', 
            'border': '1px solid #bdc3c7', 
            'borderRadius': '8px',
            'backgroundColor': '#f8f9fa'
        }),
        
        # Sección de análisis existente
        html.Hr(style={'margin': '30px 0'}),
        html.H3("📊 Análisis de Notificaciones", 
               style={'color': '#2c3e50', 'textAlign': 'center', 'marginBottom': '20px'}),
        
        html.Div([
            html.Label("Seleccionar Período:", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='periodo-dropdown',
                options=[
                    {'label': '1 Semana', 'value': '1_semana'},
                    {'label': '1 Mes', 'value': '1_mes'},
                    {'label': '3 Meses', 'value': '3_meses'}
                ],
                value='1_mes',
                style={'width': '200px'}
            )
        ], style={'margin': '20px'}),
        
        html.Div([
            html.Div([
                dcc.Graph(id='grafico-lineas')
            ], style={'width': '70%', 'display': 'inline-block'}),
            
            html.Div([
                dcc.Graph(id='grafico-dona')
            ], style={'width': '30%', 'display': 'inline-block'})
        ])
    ])
    
    @app.callback(
        [Output('grafico-lineas', 'figure'),
         Output('grafico-dona', 'figure')],
        [Input('periodo-dropdown', 'value')]
    )
    def actualizar_graficos(periodo_seleccionado):
        fig_lineas = dashboard.crear_grafico_lineas(periodo_seleccionado)
        fig_dona = dashboard.crear_grafico_dona()
        return fig_lineas, fig_dona
    
    @app.callback(
        Output('mensaje-resultado', 'children'),
        [Input('crear-notificacion-btn', 'n_clicks')],
        [State('tipo-notificacion-dropdown', 'value'),
         State('asunto-input', 'value'),
         State('cuerpo-textarea', 'value'),
         State('destinatarios-input', 'value'),
         State('fecha-programada-picker', 'date')],
        prevent_initial_call=True
    )
    def crear_nueva_notificacion(n_clicks, tipo_id, asunto, cuerpo, destinatarios, fecha_programada):
        if n_clicks is None or n_clicks == 0:
            raise PreventUpdate
        
        try:
            # Validar que se haya seleccionado un tipo
            if not tipo_id:
                return html.Div([
                    html.P("❌ Error: Debe seleccionar un tipo de notificación", 
                           style={'color': 'red', 'fontWeight': 'bold', 'margin': '0'})
                ])
            
            # Procesar fecha programada
            fecha_prog_procesada = None
            if fecha_programada:
                from datetime import datetime
                try:
                    # Convertir string de fecha a datetime
                    fecha_prog_procesada = datetime.strptime(fecha_programada, '%Y-%m-%d')
                    
                    # Validar que la fecha no sea pasada
                    if fecha_prog_procesada.date() < datetime.now().date():
                        return html.Div([
                            html.P("❌ Error: La fecha programada no puede ser anterior a hoy", 
                                   style={'color': 'red', 'fontWeight': 'bold', 'margin': '0'})
                        ])
                except ValueError:
                    return html.Div([
                        html.P("❌ Error: Formato de fecha inválido", 
                               style={'color': 'red', 'fontWeight': 'bold', 'margin': '0'})
                    ])
            
            # Crear la notificación
            exito, mensaje = dashboard.crear_notificacion(
                tipo_id=tipo_id,
                asunto=asunto or '',
                cuerpo=cuerpo or '',
                destinatarios=destinatarios or '',
                fecha_programada=fecha_prog_procesada
            )
            
            if exito:
                mensaje_adicional = ""
                if fecha_prog_procesada:
                    mensaje_adicional = f" Se enviará el {fecha_prog_procesada.strftime('%d/%m/%Y')}."
                else:
                    mensaje_adicional = " Será procesada inmediatamente."
                
                return html.Div([
                    html.P(f"✅ {mensaje}", 
                           style={'color': 'green', 'fontWeight': 'bold', 'margin': '0'}),
                    html.P(f"La notificación ha sido programada exitosamente.{mensaje_adicional}", 
                           style={'color': '#666', 'fontSize': '14px', 'margin': '5px 0 0 0'})
                ])
            else:
                return html.Div([
                    html.P(f"❌ {mensaje}", 
                           style={'color': 'red', 'fontWeight': 'bold', 'margin': '0'})
                ])
                
        except Exception as e:
            logger.error(f"Error en callback crear_nueva_notificacion: {e}")
            return html.Div([
                html.P("❌ Error interno del sistema. Revise los logs del servidor.", 
                       style={'color': 'red', 'fontWeight': 'bold', 'margin': '0'})
            ])
    
    return app

# Crear una instancia global de la aplicación Dash para ser usada externamente
app = None

def get_app():
    """Obtiene o crea la instancia de la aplicación Dash"""
    global app
    if app is None:
        app = crear_dashboard_dash()
    return app

def get_dashboard_config():
    """Obtiene la configuración del dashboard desde las variables de entorno"""
    return {
        'host': os.getenv('DASHBOARD_HOST', '0.0.0.0'),
        'port': int(os.getenv('DASHBOARD_PORT', '8050'))
    }

def generar_dashboard_simple_plotly(periodo='1_mes'):
    """
    Función simplificada para generar el dashboard sin interactividad usando solo Plotly
    """
    dashboard = DashboardNotificacionesPlotly()
    fig = dashboard.crear_dashboard_estatico(periodo)
    fig.show()
    return fig

def generar_reportes_individuales_plotly():
    """
    Genera gráficos individuales para cada período usando Plotly
    """
    dashboard = DashboardNotificacionesPlotly()
    periodos = ['1_semana', '1_mes', '3_meses']
    
    # Gráficos de líneas por período
    for periodo in periodos:
        fig = dashboard.crear_grafico_lineas(periodo)
        fig.write_html(f'notificaciones_tendencia_{periodo}.html')
        fig.show()
    
    # Gráfico de dona
    fig = dashboard.crear_grafico_dona()
    fig.write_html('notificaciones_estados.html')
    fig.show()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Iniciando Dashboard Interactivo de Notificaciones...")
    print("Características incluidas:")
    print("  📊 Análisis visual de notificaciones")
    print("  🔔 Creación de nuevas notificaciones")
    print("  📈 Gráficos en tiempo real")
    print("  🎯 Filtrado por períodos")
    
    # Dashboard interactivo con Dash (recomendado)
    app_instance = get_app()
    config = get_dashboard_config()
    
    print(f"🌐 Dashboard disponible en: http://{config['host']}:{config['port']}")
    print("💡 Presiona Ctrl+C para detener el servidor")
    
    app_instance.run(
        debug=True,
        host=config['host'], 
        port=config['port']
    )