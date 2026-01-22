# 🗓️ Event Manager - Aplicación de Gestión de Eventos

## Descripción

**Event Manager** es una aplicación web sencilla y moderna para gestionar eventos y registrar asistencias. Diseñada como un MVP (_Minimum Viable Product_), permite crear, visualizar, editar y eliminar eventos, además de registrar asistentes para cada uno.

## Características principales

- Crear eventos con nombre, lugar, fechas, color e icono
- Visualizar todos los eventos en una interfaz tipo tarjetas
- Editar y eliminar eventos (con confirmación si hay asistencias)
- Registrar asistencias por evento (nombre y timestamp)
- Interfaz responsive mobile-first optimizada para dispositivos móviles
- Diseño atractivo con Tailwind CSS y Font Awesome
- Script de despliegue automatizado para producción

## Stack Tecnológico

### Backend

- **Python 3.8+** - Lenguaje de programación principal
- **Flask 3.0** - Microframework web minimalista
- **Flask-SQLAlchemy 3.1** - ORM para manejo de bases de datos
- **SQLite** - Base de datos para desarrollo local
- **PostgreSQL** - Base de datos para producción (Railway)
- **Gunicorn** - Servidor WSGI para producción
- **Supervisor** - Gestor de procesos para mantener la app en ejecución

### Frontend

- **HTML5 + Jinja2** - Templates del servidor
- **Tailwind CSS 3.0** - Framework CSS utility-first
- **Font Awesome 6** - Iconos vectoriales
- **JavaScript Vanilla** - Interactividad básica

### Infraestructura y Despliegue

- **Nginx** - Servidor web y proxy inverso
- **Bash scripting** - Automatización de despliegue
- **Railway** - Plataforma para base de datos PostgreSQL
- **Google Cloud VM** - Entorno de producción objetivo

### Herramientas de Desarrollo

- **python-dotenv** - Manejo de variables de entorno
- **psycopg2** - Adaptador PostgreSQL para Python
- **Git** - Control de versiones
- **rsync** - Sincronización eficiente de archivos

## Estructura del Proyecto

```shell
event-manager/
├── app.py                 # Aplicación principal Flask
├── config.py              # Configuración de la app
├── requirements.txt       # Dependencias Python
├── deploy.sh             # Script de despliegue automatizado
├── .env                   # Variables de entorno (NO subir a Git)
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

## Guía de Instalación Rápida (Desarrollo Local)

### Paso 1: Clonar el Repositorio

```bash
git clone https://github.com/j2deme/event-manager.git
cd event-manager
```

Si usas GitHub Desktop puedes usar la opción de clonar repositorio, elegir la pestaña "URL" e ingresar la URL `https://github.com/j2deme/event-manager.git` o pegar el nombre del repositorio `j2deme/event-manager`.

También puedes hacer un _fork_ del repositorio para tener tu propia copia y luego clonarla.

### Paso 2: Configurar Entorno Virtual

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar (Linux/Mac)
source venv/bin/activate

# Activar (Windows)
venv\Scripts\activate
```

### Paso 3: Instalar Dependencias

Con el entorno virtual **activado**, instala las librerías necesarias:

```bash
pip install -r requirements.txt
```

### Paso 4: Configurar Variables

```bash
cp .env.example .env
# Edita el archivo .env con tus valores (SECRET_KEY es obligatoria)
nano .env  # o usa tu editor favorito
```

### Paso 5: Ejecutar la Aplicación

```bash
python app.py
```

Visita <http://localhost:5000> en tu navegador.

### Primeros Pasos en la Aplicación

1. **Crear tu primer evento**: Haz clic en "Nuevo Evento"
2. **Completa el formulario**: Nombre, fechas, lugar, color, etc.
3. **Ver detalles**: Haz clic en "Ver" en cualquier evento
4. **Registrar asistencias**: En la vista de detalle, escribe un nombre y haz clic en el botón verde
5. **Editar o eliminar**: Usa los botones correspondientes en cada evento

## Despliegue en Producción

Asumiendo que se trabaja con una VM Debian (como Google Cloud VM), este proyecto incluye un script de despliegue automatizado (`deploy.sh`) que configura todo lo necesario para ejecutar la aplicación en producción.

### Prerrequisitos para Despliegue

1. **Una VM con Debian 11/12** (o derivada como Ubuntu)
2. **Acceso SSH con privilegios de root** (o usuario con sudo)
3. **Archivo `.env` configurado** con:
   - `SECRET_KEY` para Flask
   - `DATABASE_URL` de Railway (PostgreSQL, también funciona MySQL con ajustes)

### Proceso de Despliegue Paso a Paso

#### Paso 1. Preparar el Entorno en la VM

```bash
# Conectarse a tu VM
ssh usuario@ip-de-tu-vm # O usa Google Cloud Shell con SSH

# Necesario para clonar el repo
sudo apt update && sudo apt install -y git

# Clonar el repositorio (o subir los archivos)
git clone https://github.com/j2deme/event-manager.git
cd event-manager

# Configurar el archivo .env para producción
cp .env.example .env
nano .env  # Añade SECRET_KEY y DATABASE_URL reales de Railway
```

#### Paso 2. Ejecutar el Script de Despliegue

```bash
# Dar permisos de ejecución
chmod +x deploy.sh

# Ejecutar como root (o con sudo)
sudo bash deploy.sh
```

### Paso 3. Actualizar la Aplicación (opcional)

Cuando hagas cambios en tu código:

```bash
# En tu VM, dentro del directorio del proyecto:
git pull  # O subir los cambios manualmente
sudo bash deploy.sh  # El mismo script actualizará todo
```

### ¿Qué hace el script `deploy.sh`?

El script realiza automáticamente:

1. **Instala todas las dependencias del sistema:**
   - Python 3, pip, virtualenv
   - Nginx (servidor web)
   - Supervisor (gestor de procesos)
   - rsync (sincronización de archivos)

2. **Configura el entorno de Python:**
   - Crea entorno virtual aislado
   - Instala dependencias de requirements.txt
   - Instala Gunicorn (servidor WSGI)

3. **Gestiona la configuración de forma segura:**
   - Fusión inteligente de variables `.env` (pregunta antes de sobrescribir)
   - Configura Supervisor para mantener la app en ejecución
   - Configura Nginx como proxy inverso

4. **Hace el despliegue idempotente:**
   - Solo reinstala dependencias si requirements.txt cambió
   - Solo recarga servicios si su configuración cambió
   - Puede ejecutarse múltiples veces sin efectos secundarios

5. **Proporciona verificación y monitoreo:**
   - Muestra resumen de cambios aplicados
   - Proporciona comandos útiles para gestión
   - Muestra URL de acceso y estado de servicios

### Acceso a la Aplicación Desplegada

Una vez completado el despliegue:

- **URL de acceso:** `http://IP-DE-TU-VM`
- **Ver logs de la aplicación:** `sudo tail -f /opt/event_manager/supervisor_error.log`
- **Reiniciar la app manualmente:** `sudo supervisorctl restart event_manager`

### Consideraciones de Seguridad

El script está diseñado para entornos de **práctica y desarrollo**:

- Crea un usuario dedicado (`flaskapp`) para ejecutar la aplicación
- Configura permisos restrictivos en archivos sensibles (`.env`)
- **Nota:** Para producción real, considera:
  - Configurar HTTPS con Certbot
  - Ajustar reglas de firewall
  - Implementar _hardening_ de Nginx y sistema

---

## Flujo de Trabajo Recomendado

### Para Desarrollo

```bash
# Trabaja localmente
git checkout -b nueva-funcionalidad
# ...haz tus cambios...
python app.py  # Prueba localmente
git add . && git commit -m "Descripción"
git push origin nueva-funcionalidad
```

### Para Despliegue en Producción

```bash
# En tu VM de producción
git pull origin main
sudo bash deploy.sh
# ¡Listo! Tu app está actualizada
```

---

## Solución de Problemas Comunes

### Problema: Error de base de datos PostgreSQL

**Solución:** Verifica que la variable `DATABASE_URL` en `.env` esté correctamente configurada y que el servicio de PostgreSQL esté activo.

### Problema: No uso PostgreSQL sino MySQL

**Solución:** instala el conector MySQL y ajusta la variable `DATABASE_URL` en `.env`:

```bash
pip install mysql-connector-python
```

Y cambia la línea en `.env` a:

```env
DATABASE_URL=mysql+mysqlconnector://usuario:password@host:puerto/nombre_db
```

### Problema: Error "connection refused" al acceder a la app

**Solución:** Verifica que el puerto 80 esté abierto en el firewall de tu proveedor cloud.

### Problema: La app no se reinicia después del despliegue

**Solución:** Verifica los logs de Supervisor:

```bash
sudo supervisorctl status event_manager
sudo tail -f /opt/event_manager/supervisor_error.log
```

### Problema: Error de permisos en archivos

**Solución:** Asegura los permisos correctos:

```bash
sudo chown -R flaskapp:flaskapp /opt/event_manager
sudo chmod 600 /opt/event_manager/.env
```

### Problema: Nginx no sirve archivos estáticos

**Solución:** Verifica la configuración de Nginx:

```bash
sudo nginx -t  # Verifica sintaxis
sudo systemctl restart nginx
```

---

## Soporte y Contribuciones

Si encuentras problemas o quieres contribuir:

1. Revisa la sección de **Solución de Problemas** arriba
2. Verifica los logs de la aplicación y servicios
3. Asegúrate de seguir los pasos exactamente como se describen
4. **Si persiste el problema**, crea un issue en el repositorio con:
   - Descripción detallada del problema
   - Pasos para reproducirlo
   - Mensajes de error completos
   - Entorno (sistema operativo, versión de Python, etc.)

---

## ⚠️ Disclaimer / Aviso Legal

**Event Manager** es un **proyecto educativo** desarrollado como parte de una práctica de despliegue de aplicaciones web en la nube. Su propósito principal es demostrar la integración de tecnologías como Flask, PostgreSQL (MySQL), Nginx y Gunicorn, así como la automatización del despliegue mediante scripts Bash.

### Limitación de Responsabilidad

1. **"AS IS" / TAL CUAL**: Este proyecto se proporciona **"TAL CUAL" ("AS IS")**, sin garantías de ningún tipo, ya sean expresas o implícitas.
2. **Propósito Educativo**: Este código está destinado **exclusivamente a fines de aprendizaje y demostración**. No está auditado para cumplir con estándares de seguridad, rendimiento o mejores prácticas de producción empresarial.
3. **Uso en Producción bajo su Propio Riesgo**: Si decides utilizar este código o partes de él en un entorno de producción, lo haces **bajo tu entera responsabilidad**. Se recomienda encarecidamente:
   - Realizar una auditoría de seguridad exhaustiva.
   - Ajustar la configuración (especialmente en `config.py`, `.env` y los scripts de despliegue) según las necesidades y políticas de seguridad de tu organización.
   - Implementar medidas adicionales como HTTPS (SSL/TLS), sistemas de backup, monitoreo y un plan de recuperación ante desastres.

4. **Contribuciones y Issues**: Se agradecen las contribuciones y reportes de problemas relacionados con el **ámbito educativo** del proyecto. Sin embargo, no se ofrece soporte técnico para implementaciones personalizadas o problemas derivados de modificaciones al código base.

**En resumen: Este es un ejercicio de aprendizaje. Úsalo como referencia, inspiración o punto de partida, pero adapta y fortalece cada componente críticamente antes de considerarlo para un uso real.**

---

¡Feliz despliegue! 🚀
