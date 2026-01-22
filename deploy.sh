#!/bin/bash
# deploy.sh - Script para desplegar/actualizar Flask app con fusión segura de .env
# Estrategia: Compara .env local vs producción, pregunta antes de sobrescribir valores existentes.

set -e

# ============================================
# 1. VARIABLES Y FUNCIONES (INICIALIZACIÓN COMPLETA)
# ============================================
APP_NAME="event_manager"
APP_USER="flaskapp"
APP_DIR="/opt/$APP_NAME"
LOCAL_ENV=".env"
PROD_ENV="$APP_DIR/.env"

# Variables de control
NEW_KEYS=""
DIFF_KEYS=""
NEED_SUPERVISOR_RELOAD=0
NEED_NGINX_RELOAD=0
REQUIREMENTS_CHANGED=0

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

config_changed() {
    local config_file="$1"
    local temp_file="$2"
    
    # Si no existe el archivo destino, sí hay cambio
    [[ ! -f "$config_file" ]] && return 0
    
    # Comparar contenido con archivo temporal
    if ! diff -q "$config_file" "$temp_file" > /dev/null 2>&1; then
        return 0  # Hay cambios
    else
        return 1  # No hay cambios
    fi
}

# Función para extraer nombres de variables de un archivo .env
extract_keys() {
    grep -v '^#' "$1" | grep -v '^$' | cut -d'=' -f1 | sort
}

# Función para extraer el valor de una clave específica
get_value() {
    grep "^$1=" "$2" 2>/dev/null | cut -d'=' -f2- | head -1
}

# ============================================
# 2. VERIFICACIÓN INICIAL
# ============================================
if [[ $EUID -ne 0 ]]; then
    echo "❌ Ejecuta con: sudo bash $0"
    exit 1
fi

if [[ ! -f "$LOCAL_ENV" ]]; then
    log "❌ ERROR: No se encontró '$LOCAL_ENV' en el directorio actual."
    log "   Crea el archivo a partir de .env.example y configúralo."
    exit 1
fi

# Verificación básica del .env local
if ! grep -q "SECRET_KEY=" "$LOCAL_ENV" || ! grep -q "DATABASE_URL=" "$LOCAL_ENV"; then
    log "⚠️  ADVERTENCIA: $LOCAL_ENV parece no tener SECRET_KEY o DATABASE_URL."
    log "   La aplicación podría fallar. ¿Continuar? (s/N)"
    read -r respuesta
    [[ "$respuesta" =~ ^[Ss] ]] || exit 1
fi

# ============================================
# 3. PREPARACIÓN DEL SISTEMA Y DEPENDENCIAS
# ============================================
log "🔧 Preparando sistema e instalando dependencias..."

# Actualizar lista de paquetes
log "   📦 Actualizando lista de paquetes disponibles..."
apt-get update > /dev/null 2>&1

# Instalar paquetes esenciales de forma segura y silenciosa
log "   📦 Instalando herramientas requeridas (rsync, python3, nginx, supervisor)..."
apt-get install -y --no-install-recommends \
    rsync \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    supervisor \
    curl > /dev/null 2>&1

log "✅ Dependencias del sistema instaladas."

# ============================================
# 4. SINCRONIZAR CÓDIGO
# ============================================
log "🔄 Sincronizando código..."
if ! id "$APP_USER" &>/dev/null; then
    useradd -r -s /bin/bash -m -d "$APP_DIR" "$APP_USER"
    log "  👤 Usuario $APP_USER creado."
fi

mkdir -p "$APP_DIR"
# Usar rsync sin --progress para output más limpio
rsync -av --exclude='.env' --exclude='venv/' --exclude='*.log' --exclude='*.sock' --exclude='.requirements_hash' \
      --delete . "$APP_DIR/" > /dev/null 2>&1
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
log "✅ Código sincronizado."

# ============================================
# 5. LÓGICA PRINCIPAL: FUSIÓN SEGURA DE .env
# ============================================
log "🔍 Analizando configuración de entorno..."

# Si no existe .env en producción, copiar el local completo
if [[ ! -f "$PROD_ENV" ]]; then
    log "📄 Primera vez: Copiando $LOCAL_ENV a producción..."
    cp "$LOCAL_ENV" "$PROD_ENV"
    chown "$APP_USER:$APP_USER" "$PROD_ENV"
    chmod 600 "$PROD_ENV"
else
    # COMPARACIÓN AVANZADA: Local vs Producción
    log "🔄 Comparando variables de entorno..."
    
    # Extraer claves de ambos archivos
    LOCAL_KEYS=$(extract_keys "$LOCAL_ENV")
    PROD_KEYS=$(extract_keys "$PROD_ENV")
    
    # 1. Encontrar claves NUEVAS en local (no existen en producción)
    NEW_KEYS=$(comm -13 <(echo "$PROD_KEYS") <(echo "$LOCAL_KEYS") 2>/dev/null || echo "")
    
    # 2. Encontrar claves COMUNES con valores diferentes
    DIFF_KEYS=""
    for key in $(comm -12 <(echo "$PROD_KEYS") <(echo "$LOCAL_KEYS") 2>/dev/null || echo ""); do
        local_val=$(get_value "$key" "$LOCAL_ENV")
        prod_val=$(get_value "$key" "$PROD_ENV")
        if [[ "$local_val" != "$prod_val" ]]; then
            DIFF_KEYS="$DIFF_KEYS$key|"
        fi
    done
    
    # Si hay cambios, mostrar reporte y preguntar
    if [[ -n "$NEW_KEYS" ]] || [[ -n "$DIFF_KEYS" ]]; then
        log "📋 Se detectaron diferencias en .env:"
        
        if [[ -n "$NEW_KEYS" ]]; then
            log "   📌 Variables NUEVAS en local (faltan en producción):"
            for key in $NEW_KEYS; do
                log "      - $key=$(get_value "$key" "$LOCAL_ENV")"
            done
        fi
        
        if [[ -n "$DIFF_KEYS" ]]; then
            log "   ⚠️  Variables con VALORES DIFERENTES:"
            IFS='|' read -ra diff_array <<< "$DIFF_KEYS"
            for key in "${diff_array[@]}"; do
                [[ -z "$key" ]] && continue
                log "      - $key:"
                log "          Producción: $(get_value "$key" "$PROD_ENV")"
                log "          Local (nuevo): $(get_value "$key" "$LOCAL_ENV")"
            done
        fi
        
        log ""
        log "¿Cómo quieres proceder?"
        echo "  1) Aplicar TODOS los cambios del local a producción (sobrescribir)"
        echo "  2) Solo agregar NUEVAS variables (no tocar valores existentes)"
        echo "  3) Mantener producción como está (no cambiar nada)"
        echo "  4) Salir y revisar manualmente"
        echo ""
        read -p "Selecciona opción (1-4): " -r opcion
        
        case $opcion in
            1)
                # Opción 1: Sobrescribir completo (local es fuente de verdad)
                log "✅ Sobrescribiendo $PROD_ENV con versión local..."
                cp "$LOCAL_ENV" "$PROD_ENV"
                ;;
            2)
                # Opción 2: Solo agregar nuevas variables (fusionar)
                log "✅ Agregando solo variables nuevas..."
                temp_env=$(mktemp)
                cp "$PROD_ENV" "$temp_env"
                
                for key in $NEW_KEYS; do
                    local_val=$(get_value "$key" "$LOCAL_ENV")
                    # Si la variable no existe en producción, agregarla
                    if ! grep -q "^$key=" "$temp_env" 2>/dev/null; then
                        echo "$key=$local_val" >> "$temp_env"
                        log "      + Añadida: $key"
                    fi
                done
                
                mv "$temp_env" "$PROD_ENV"
                ;;
            3)
                log "ℹ️  Manteniendo $PROD_ENV sin cambios."
                ;;
            4)
                log "❌ Saliendo. Revisa los archivos manualmente."
                exit 1
                ;;
            *)
                log "⚠️  Opción inválida. Manteniendo producción sin cambios."
                ;;
        esac
        
        # Proteger archivo después de cambios
        chown "$APP_USER:$APP_USER" "$PROD_ENV" 2>/dev/null || true
        chmod 600 "$PROD_ENV" 2>/dev/null || true
    else
        log "✅ Los archivos .env son consistentes. No hay cambios que aplicar."
    fi
fi

# ============================================
# 6. CONFIGURAR ENTORNO Y SERVICIOS
# ============================================
log "🐍 Configurando Python..."
if [[ ! -d "$APP_DIR/venv" ]]; then
    sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"
    log "  🆕 Entorno virtual creado."
fi

# Verificar si requirements.txt cambió
REQUIREMENTS_FILE="$APP_DIR/requirements.txt"
REQUIREMENTS_HASH_FILE="$APP_DIR/.requirements_hash"

current_hash=""
stored_hash=""

if [[ -f "$REQUIREMENTS_FILE" ]]; then
    current_hash=$(md5sum "$REQUIREMENTS_FILE" 2>/dev/null | cut -d' ' -f1)
    stored_hash=$(cat "$REQUIREMENTS_HASH_FILE" 2>/dev/null || echo "")
fi

# Si no hay dependencias instaladas o el hash cambió, reinstalar
if [[ -z "$current_hash" ]] || [[ "$current_hash" != "$stored_hash" ]] || \
   [[ ! -f "$APP_DIR/venv/bin/gunicorn" ]]; then
    REQUIREMENTS_CHANGED=1
    log "📦 Instalando/actualizando dependencias Python..."
    sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --quiet --upgrade pip
    sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --quiet -r "$REQUIREMENTS_FILE"
    sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --quiet gunicorn
    
    # Guardar nuevo hash solo si requirements.txt existe
    if [[ -f "$REQUIREMENTS_FILE" ]]; then
        echo "$current_hash" > "$REQUIREMENTS_HASH_FILE"
        chown "$APP_USER:$APP_USER" "$REQUIREMENTS_HASH_FILE"
    fi
    log "✅ Dependencias actualizadas."
else
    log "ℹ️  Dependencias Python ya están actualizadas."
fi

# ============================================
# 7. CONFIGURAR SUPERVISOR
# ============================================
log "🔧 Configurando Supervisor..."
SUPERVISOR_CONF="/etc/supervisor/conf.d/$APP_NAME.conf"
SUPERVISOR_TEMP=$(mktemp)

cat > "$SUPERVISOR_TEMP" << EOF
[program:$APP_NAME]
command=$APP_DIR/venv/bin/gunicorn --workers 3 --bind unix:$APP_DIR/$APP_NAME.sock --timeout 120 app:app
directory=$APP_DIR
user=$APP_USER
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
environment=PATH="$APP_DIR/venv/bin",HOME="$APP_DIR"
stdout_logfile=$APP_DIR/supervisor.log
stderr_logfile=$APP_DIR/supervisor_error.log
EOF

if config_changed "$SUPERVISOR_CONF" "$SUPERVISOR_TEMP"; then
    log "  📝 Actualizando configuración de Supervisor..."
    mv "$SUPERVISOR_TEMP" "$SUPERVISOR_CONF"
    NEED_SUPERVISOR_RELOAD=1
else
    log "  ℹ️  Supervisor: Configuración sin cambios."
    rm -f "$SUPERVISOR_TEMP"
fi

# ============================================
# 8. CONFIGURAR NGINX
# ============================================
log "🌐 Configurando Nginx..."
NGINX_CONF="/etc/nginx/sites-available/$APP_NAME"
NGINX_TEMP=$(mktemp)

cat > "$NGINX_TEMP" << EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://unix:$APP_DIR/$APP_NAME.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static {
        alias $APP_DIR/static;
        expires 30d;
    }
}
EOF

if config_changed "$NGINX_CONF" "$NGINX_TEMP"; then
    log "  📝 Actualizando configuración de Nginx..."
    mv "$NGINX_TEMP" "$NGINX_CONF"
    NEED_NGINX_RELOAD=1
else
    log "  ℹ️  Nginx: Configuración sin cambios."
    rm -f "$NGINX_TEMP"
fi

# Crear enlace simbólico (idempotente)
ln -sf "/etc/nginx/sites-available/$APP_NAME" "/etc/nginx/sites-enabled/" 2>/dev/null || true
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

# ============================================
# 9. APLICAR CAMBIOS EN SERVICIOS
# ============================================
# A. Recargar Supervisor solo si hubo cambios en su configuración
if [[ $NEED_SUPERVISOR_RELOAD -eq 1 ]]; then
    log "🔄 Recargando configuración de Supervisor..."
    supervisorctl reread > /dev/null 2>&1
    supervisorctl update > /dev/null 2>&1
fi

# B. Gestionar la aplicación (reiniciar solo si es necesario)
APP_STATUS=$(supervisorctl status "$APP_NAME" 2>/dev/null | awk '{print $2}' || echo "NOT_RUNNING")

if [[ "$APP_STATUS" == "RUNNING" ]]; then
    # Si Supervisor cambió O requirements cambiaron O primera vez
    if [[ $NEED_SUPERVISOR_RELOAD -eq 1 ]] || [[ $REQUIREMENTS_CHANGED -eq 1 ]]; then
        log "🔁 Reiniciando aplicación (cambios detectados)..."
        supervisorctl restart "$APP_NAME" > /dev/null 2>&1
        log "✅ Aplicación reiniciada."
    else
        log "ℹ️  Aplicación ya está ejecutándose (sin cambios necesarios)."
    fi
elif [[ "$APP_STATUS" == "STOPPED" ]] || [[ "$APP_STATUS" == "NOT_RUNNING" ]]; then
    log "🚀 Iniciando aplicación..."
    supervisorctl start "$APP_NAME" > /dev/null 2>&1
    log "✅ Aplicación iniciada."
else
    log "⚠️  Estado de aplicación desconocido: $APP_STATUS"
    log "  Intentando iniciar..."
    supervisorctl start "$APP_NAME" > /dev/null 2>&1 || true
fi

# C. Recargar Nginx solo si hubo cambios en su configuración
if [[ $NEED_NGINX_RELOAD -eq 1 ]]; then
    log "🔃 Recargando Nginx..."
    if nginx -t > /dev/null 2>&1; then
        systemctl reload nginx > /dev/null 2>&1
        log "✅ Nginx recargado."
    else
        log "❌ Error en configuración de Nginx. Verifica con: nginx -t"
    fi
fi

# ============================================
# 10. VERIFICACIÓN FINAL
# ============================================
log "🎉 ¡Despliegue completado!"
log ""

# Resumen de cambios aplicados
log "📊 RESUMEN DE CAMBIOS APLICADOS:"
[[ -n "$NEW_KEYS" ]] && log "   • Variables nuevas en .env: $(echo "$NEW_KEYS" | tr '\n' ' ')"
[[ -n "$DIFF_KEYS" ]] && log "   • Variables actualizadas en .env: $(echo "$DIFF_KEYS" | tr '|' ' ')"
[[ $NEED_SUPERVISOR_RELOAD -eq 1 ]] && log "   • Supervisor: Configuración actualizada y recargada"
[[ $NEED_NGINX_RELOAD -eq 1 ]] && log "   • Nginx: Configuración actualizada y recargada"
[[ $REQUIREMENTS_CHANGED -eq 1 ]] && log "   • Python: Dependencias actualizadas"

# Estado actual del sistema
log ""
log "🔍 ESTADO ACTUAL:"
log "   • Aplicación: $(supervisorctl status "$APP_NAME" 2>/dev/null | awk '{print $2 " (" $1 ")"}' || echo "Desconocido")"
log "   • Directorio: $APP_DIR"
log "   • Usuario: $APP_USER"

# Mostrar URL de acceso
IP_ADDRESS=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")
log "🌐 URL de acceso: http://$IP_ADDRESS"
log ""

# Comandos útiles
log "📝 COMANDOS ÚTILES:"
log "   • Ver logs de la app:    sudo tail -f $APP_DIR/supervisor_error.log"
log "   • Reiniciar manualmente: sudo supervisorctl restart $APP_NAME"
log "   • Ver estado:            sudo supervisorctl status"
log "   • Ver logs de Nginx:     sudo journalctl -u nginx --since '5 minutes ago'"