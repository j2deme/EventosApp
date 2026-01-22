# 🗓️ Event Manager - Aplicación de Gestión de Eventos

## Descripción

**Event Manager** es una aplicación web sencilla y moderna para gestionar eventos y registrar asistencias. Diseñada como un MVP (_Minimum Viable Product_), permite crear, visualizar, editar y eliminar eventos, además de registrar asistentes para cada uno.

**Características principales:**

- ✅ Crear eventos con nombre, lugar, fechas, color e icono
- ✅ Visualizar todos los eventos en una interfaz tipo tarjetas
- ✅ Editar y eliminar eventos (con confirmación si hay asistencias)
- ✅ Registrar asistencias por evento (nombre y timestamp)
- ✅ Interfaz responsive mobile-first optimizada para dispositivos móviles
- ✅ Diseño atractivo con Tailwind CSS y Font Awesome

## Stack Tecnológico

### **Backend:**

- **Python 3.8+** - Lenguaje de programación principal
- **Flask 3.0** - Microframework web minimalista
- **Flask-SQLAlchemy 3.1** - ORM para manejo de bases de datos
- **SQLite** - Base de datos para desarrollo local
- **PostgreSQL** - Base de datos para producción (Railway)

### **Frontend:**

- **HTML5 + Jinja2** - Templates del servidor
- **Tailwind CSS 3.0** - Framework CSS utility-first
- **Font Awesome 6** - Iconos vectoriales
- **JavaScript Vanilla** - Interactividad básica

### **Herramientas de Desarrollo:**

- **python-dotenv** - Manejo de variables de entorno
- **psycopg2** - Adaptador PostgreSQL para Python
- **Git** - Control de versiones

## Estructura del Proyecto

```shell
event-manager/
├── app.py                 # Aplicación principal Flask
├── config.py              # Configuración de la app
├── requirements.txt       # Dependencias Python
├── .env                   # Variables de entorno
├── .env.example          # Ejemplo de variables de entorno
├── app.db                # Base de datos SQLite (Local)
├── static/
│   └── css/
│       └── style.css     # Estilos CSS adicionales
└── templates/
    ├── base.html         # Plantilla base
    ├── eventos/          # Vistas de eventos
    └── asistencias/      # Vistas de asistencias
```

## Guía de Instalación

### Paso 1: Clonar el Repositorio

1. **Abre tu terminal o línea de comandos**
2. **Ve a la carpeta donde quieres guardar el proyecto**, por ejemplo:

   ```bash
   cd ~/Desktop  # Para escritorio en Mac/Linux
   cd Desktop    # Para escritorio en Windows (CMD)
   ```

3. **Clona el repositorio**:

   ```bash
   git clone https://github.com/j2deme/event-manager.git
   ```

   Si usas GitHub Desktop puedes usar la opción de clonar repositorio, elegir la pestaña "URL" e ingresar la URL `https://github.com/j2deme/event-manager.git` o pegar el nombre del repositorio `j2deme/event-manager`.

   También puedes hacer un _fork_ del repositorio para tener tu propia copia.

4. **Accede a la carpeta del proyecto**:

   ```bash
   cd event-manager
   ```

### Paso 2: Crear y Activar un Entorno Virtual (Recomendado)

**¿Por qué un entorno virtual?** Para aislar las dependencias de este proyecto y no mezclarlas con otros proyectos Python.

#### **Para Windows:**

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
venv\Scripts\activate
```

Verás `(venv)` al principio de tu línea de comandos cuando esté activado.

#### **Para Mac/Linux:**

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate
```

### Paso 3: Instalar Dependencias

Con el entorno virtual **activado**, instala las librerías necesarias:

```bash
pip install -r requirements.txt
```

Si ves algún error, intenta con:

```bash
pip install flask python-dotenv psycopg2-binary
```

### Paso 4: Configurar Variables de Entorno

1. **Localiza el archivo `.env.example`** en la carpeta del proyecto
2. **Crea una copia** y renómbrala como `.env`:

   #### **Para Windows (PowerShell):**

   ```powershell
   Copy-Item .env.example .env
   ```

   #### **Para Mac/Linux:**

   ```bash
   cp .env.example .env
   ```

   O puedes copiar y pegar el archivo de manera gráfica.

3. **Edita el archivo `.env`** con un editor de texto (Bloc de Notas, VS Code, etc.):

   ```env
   # Clave secreta para seguridad de la app (puedes cambiarla)
   SECRET_KEY=mi-clave-secreta-super-segura-123

   # Para desarrollo local DEJA ESTA LÍNEA COMENTADA (usará SQLite)
   # DATABASE_URL=postgresql://usuario:password@host:puerto/nombre_db
   ```

   > **¡IMPORTANTE!** Deja comentada la línea de `DATABASE_URL` (con `#` al inicio) para usar SQLite localmente.

### Paso 5: Inicializar la Base de Datos

La aplicación creará automáticamente una base de datos SQLite local (`app.db`) al iniciarse por primera vez.

### Paso 6: Ejecutar la Aplicación

**Método 1 - Simple:**

```bash
python app.py
```

**Método 2 - Con recarga automática** (recomendado para desarrollo):

```bash
# Configurar variables
$env:FLASK_APP = "app.py"  # Windows PowerShell
set FLASK_APP=app.py       # Windows CMD
export FLASK_APP=app.py    # Mac/Linux

# Ejecutar en modo desarrollo
flask run --debug
```

### Paso 7: Acceder a la Aplicación

Una vez que el servidor esté ejecutándose, verás un mensaje similar a:

```shell
* Running on http://127.0.0.1:5000
* Running on http://localhost:5000
```

**Abre tu navegador web y visita:**

- <http://localhost:5000>
- <http://127.0.0.1:5000>

### Primeros Pasos en la Aplicación

1. **Crear tu primer evento**: Haz clic en "Nuevo Evento"
2. **Completa el formulario**: Nombre, fechas, lugar, color, etc.
3. **Ver detalles**: Haz clic en "Ver" en cualquier evento
4. **Registrar asistencias**: En la vista de detalle, escribe un nombre y haz clic en el botón verde
5. **Editar o eliminar**: Usa los botones correspondientes en cada evento

## Solución de Problemas Comunes

### **Problema:** Error "ModuleNotFoundError: No module named 'flask'"

**Solución:** Asegúrate de que el entorno virtual está activado y las dependencias instaladas:

```bash
# Activar entorno
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Instalar Flask
pip install flask
```

### **Problema:** Error de puerto en uso

**Solución:** Cambia el puerto:

```bash
python app.py --port 5001
```

### **Problema:** No se ven los estilos CSS

**Solución:** Presiona Ctrl+F5 para limpiar la caché del navegador

### **Problema:** Error de base de datos PostgreSQL

**Solución:** Verifica que la variable `DATABASE_URL` en `.env` esté correctamente configurada y que el servicio de PostgreSQL esté activo.

## **Problema:** No uso PostgreSQL sino MySQL

**Solución:** instala el conector MySQL y ajusta la variable `DATABASE_URL` en `.env`:

```bash
pip install mysql-connector-python
```

Y cambia la línea en `.env` a:

```env
DATABASE_URL=mysql+mysqlconnector://usuario:password@host:puerto/nombre_db
```

## Comandos Útiles

```bash
# Activar entorno virtual
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# Desactivar entorno virtual
deactivate

# Ver dependencias instaladas
pip list

# Actualizar requirements.txt
pip freeze > requirements.txt

# Ejecutar la app
python app.py
```

## Soporte

Si encuentras problemas:

1. Verifica que todos los pasos de instalación se siguieron correctamente
2. Revisa que el archivo `.env` existe y tiene la configuración correcta
3. Asegúrate de que el entorno virtual está activado
4. Comprueba que no hay errores en la terminal al ejecutar `python app.py`
