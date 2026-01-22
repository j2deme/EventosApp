from werkzeug.exceptions import ServiceUnavailable
from sqlalchemy.exc import OperationalError, DatabaseError
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import os
import locale
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app, engine_options={'pool_recycle': 300})

# ============================================
# MANEJADOR GLOBAL DE ERRORES DE CONEXIÓN A BD
# ============================================


@app.errorhandler(OperationalError)
@app.errorhandler(DatabaseError)
def handle_database_error(error):
    """
    Intercepta errores de conexión a la base de datos y muestra
    una página amigable al usuario en lugar del error crudo.

    Esto maneja casos como:
    - Railway PostgreSQL en estado "dormido" o iniciando
    - Conexiones perdidas por timeout
    - Servidor de BD no disponible
    """

    # Log del error real (para debugging, no se muestra al usuario)
    app.logger.error(f"Error de conexión a BD: {str(error)}")

    # Verificar si es un error de conexión (patrones comunes)
    error_msg = str(error).lower()
    connection_keywords = [
        'connection', 'connect', 'conexión', 'conectar',
        'database system is not yet accepting connections',
        'server closed the connection',
        'could not connect to server',
        'timeout expired',
        'network'
    ]

    is_connection_error = any(
        keyword in error_msg for keyword in connection_keywords)

    if is_connection_error:
        # Devolver una página HTML amigable con código 503 (Servicio No Disponible)
        return render_template(
            'errors/database_unavailable.html',
            error_message="La base de datos está temporalmente no disponible",
            recovery_message="Esto suele ocurrir cuando el servicio en la nube está iniciando. Por favor, intenta de nuevo en unos segundos."
        ), 503
    else:
        # Para otros errores de BD, mostrar una página genérica
        return render_template(
            'errors/database_error.html',
            error_message="Ha ocurrido un error inesperado con la base de datos"
        ), 500

# ============================================
# MANEJADOR PARA ERROR 503 (SERVICE UNAVAILABLE)
# ============================================


@app.errorhandler(503)
def service_unavailable(error):
    """Manejador específico para errores 503"""
    return render_template('errors/service_unavailable.html'), 503

# ============================================
# MIDDLEWARE: Verificar conexión antes de ciertas rutas
# ============================================


@app.before_request
def check_database_connection():
    """
    Middleware opcional que verifica la conexión antes de rutas críticas.
    Útil para endpoints de escritura (POST, PUT, DELETE).
    """

    # Solo verificar en métodos que modifican datos
    if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
        try:
            # Intenta una consulta simple para verificar la conexión
            from sqlalchemy import text
            db.session.execute(text('SELECT 1')).fetchall()
        except Exception as e:
            # Si falla, redirigir a una página informativa
            app.logger.warning(
                f"Conexión a BD no disponible para {request.path}: {str(e)}")

            # Para AJAX/API, devolver JSON
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({
                    'error': 'database_unavailable',
                    'message': 'La base de datos no está disponible temporalmente',
                    'retry_after': 30  # Segundos
                }), 503

            # Para navegadores, redirigir a página informativa
            return redirect(url_for('database_unavailable_page'))


# Configurar locale para español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    app.logger.info("Locale español configurado: es_ES.UTF-8")
except locale.Error:
    try:
        # Fallback 1: Intentar con formato más común
        locale.setlocale(locale.LC_TIME, 'es_ES.utf8')
        app.logger.info("Locale español configurado: es_ES.utf8")
    except locale.Error:
        try:
            # Fallback 2: Intentar locale genérico
            locale.setlocale(locale.LC_TIME, 'es_ES')
            app.logger.info("Locale español configurado: es_ES")
        except locale.Error:
            # Fallback 3: Si nada funciona, usar locale del sistema y continuar
            app.logger.warning(
                "Locale español no disponible. Usando configuración regional por defecto.")
            pass  # Continuar sin configurar locale

# Modelos


class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    lugar = db.Column(db.String(200))
    fecha_inicio = db.Column(db.DateTime, nullable=False)
    fecha_fin = db.Column(db.DateTime, nullable=False)
    color = db.Column(db.String(7), default='#3B82F6')  # Código HEX
    icono = db.Column(db.String(50), default='calendar')
    creado_en = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc))
    asistencias = db.relationship(
        'Asistencia', backref='evento', cascade='all, delete-orphan', lazy=True)


class Asistencia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    evento_id = db.Column(db.Integer, db.ForeignKey(
        'evento.id'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc))

# Rutas de Eventos


@app.route('/')
def index():
    return redirect(url_for('listar_eventos'))


@app.route('/eventos')
def listar_eventos():
    eventos = Evento.query.order_by(Evento.fecha_inicio.asc()).all()
    return render_template('eventos/list.html', eventos=eventos)


@app.route('/eventos/crear', methods=['GET', 'POST'])
def crear_evento():
    if request.method == 'POST':
        try:
            evento = Evento()
            evento.nombre = request.form['nombre']
            evento.lugar = request.form['lugar']
            evento.fecha_inicio = datetime.strptime(
                request.form['fecha_inicio'], '%Y-%m-%dT%H:%M')
            evento.fecha_fin = datetime.strptime(
                request.form['fecha_fin'], '%Y-%m-%dT%H:%M')
            evento.color = request.form.get('color', '#3B82F6')
            evento.icono = request.form.get('icono', 'calendar')
            db.session.add(evento)
            db.session.commit()
            flash('Evento creado exitosamente', 'success')
            return redirect(url_for('listar_eventos'))
        except Exception as e:
            flash(f'Error al crear evento: {str(e)}', 'error')

    return render_template('eventos/create.html')


@app.route('/eventos/<int:id>/editar', methods=['GET', 'POST'])
def editar_evento(id):
    evento = Evento.query.get_or_404(id)

    if request.method == 'POST':
        try:
            evento.nombre = request.form['nombre']
            evento.lugar = request.form['lugar']
            evento.fecha_inicio = datetime.strptime(
                request.form['fecha_inicio'], '%Y-%m-%dT%H:%M')
            evento.fecha_fin = datetime.strptime(
                request.form['fecha_fin'], '%Y-%m-%dT%H:%M')
            evento.color = request.form.get('color', '#3B82F6')
            evento.icono = request.form.get('icono', 'calendar')

            db.session.commit()
            flash('Evento actualizado exitosamente', 'success')
            return redirect(url_for('detalle_evento', id=id))
        except Exception as e:
            flash(f'Error al actualizar evento: {str(e)}', 'error')

    return render_template('eventos/edit.html', evento=evento)


@app.route('/eventos/<int:id>')
def detalle_evento(id):
    evento = Evento.query.get_or_404(id)
    return render_template('eventos/detail.html', evento=evento)


@app.route('/eventos/<int:id>/eliminar', methods=['POST'])
def eliminar_evento(id):
    evento = Evento.query.get_or_404(id)

    if request.method == 'POST':
        try:
            # Verificar si hay asistencias
            tiene_asistencias = len(evento.asistencias) > 0

            if tiene_asistencias and not request.form.get('confirmar_borrado'):
                flash(
                    'Este evento tiene asistencias registradas. Confirma el borrado.', 'warning')
                return render_template('eventos/detail.html', evento=evento, mostrar_confirmacion=True)

            db.session.delete(evento)
            db.session.commit()
            flash('Evento eliminado exitosamente', 'success')
            return redirect(url_for('listar_eventos'))
        except Exception as e:
            flash(f'Error al eliminar evento: {str(e)}', 'error')

    return redirect(url_for('detalle_evento', id=id))

# Rutas de Asistencias


@app.route('/eventos/<int:evento_id>/asistencias')
def listar_asistencias(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    return render_template('asistencias/list.html', evento=evento)


@app.route('/eventos/<int:evento_id>/asistencias/registrar', methods=['POST'])
def registrar_asistencia(evento_id):
    try:
        asistencia = Asistencia()
        asistencia.evento_id = evento_id
        asistencia.nombre = request.form['nombre']
        db.session.add(asistencia)
        db.session.commit()
        flash('Asistencia registrada exitosamente', 'success')
    except Exception as e:
        flash(f'Error al registrar asistencia: {str(e)}', 'error')

    return redirect(url_for('listar_asistencias', evento_id=evento_id))


@app.route('/asistencias/<int:id>/eliminar', methods=['POST'])
def eliminar_asistencia(id):
    asistencia = Asistencia.query.get_or_404(id)
    evento_id = asistencia.evento_id

    try:
        db.session.delete(asistencia)
        db.session.commit()
        flash('Asistencia eliminada exitosamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar asistencia: {str(e)}', 'error')

    return redirect(url_for('listar_asistencias', evento_id=evento_id))

# API para datos JSON (opcional)


@app.route('/api/eventos')
def api_eventos():
    eventos = Evento.query.all()
    return jsonify([{
        'id': e.id,
        'nombre': e.nombre,
        'lugar': e.lugar,
        'fecha_inicio': e.fecha_inicio.isoformat(),
        'fecha_fin': e.fecha_fin.isoformat(),
        'color': e.color,
        'icono': e.icono
    } for e in eventos])


if __name__ == '__main__':
    try:
        with app.app_context():
            db.create_all()
            print("✅ Tablas verificadas/creadas exitosamente.")
    except Exception as e:
        print(f"⚠️  Advertencia al crear tablas: {e}")
        print("La aplicación continuará iniciándose, pero verifica la conexión a la base de datos.")

    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Servidor iniciado en http://0.0.0.0:{port}")
    app.run(debug=True, host='0.0.0.0', port=port)
