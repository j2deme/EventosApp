from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import os
import locale
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app, engine_options={'pool_recycle': 300})

# Configurar locale para español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')  # Windows

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
