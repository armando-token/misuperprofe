#!/bin/bash

# Script de backup automático para MiSuperProfe
# Este script protege los datos durante reinicios del servidor

BACKUP_DIR="${BACKUP_DIR:-/home/ubuntu/backups}"
DB_NAME="${POSTGRES_DB:-mysuper_bd}"
DB_USER="${POSTGRES_USER:-mysuper_user}"
DB_PASSWORD="${POSTGRES_PASSWORD:-}"
DATE=$(date +%Y%m%d_%H%M%S)

echo "🔄 INICIANDO BACKUP AUTOMÁTICO - $(date)"
echo "=================================================="

# Crear directorio de backup si no existe
mkdir -p "$BACKUP_DIR"

# Backup de PostgreSQL
echo "📊 Creando backup de PostgreSQL..."
PG_BACKUP_FILE="$BACKUP_DIR/postgres_backup_$DATE.sql"

docker-compose exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > "$PG_BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Backup PostgreSQL creado: $PG_BACKUP_FILE"
    echo "   Tamaño: $(du -h "$PG_BACKUP_FILE" | cut -f1)"
else
    echo "❌ Error en backup PostgreSQL"
    exit 1
fi

# Backup de Redis
echo "📊 Creando backup de Redis..."
REDIS_BACKUP_FILE="$BACKUP_DIR/redis_backup_$DATE.rdb"

docker-compose exec -T redis redis-cli BGSAVE
sleep 2  # Esperar a que termine el BGSAVE
docker cp misuperredis:/data/dump.rdb "$REDIS_BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Backup Redis creado: $REDIS_BACKUP_FILE"
    echo "   Tamaño: $(du -h "$REDIS_BACKUP_FILE" | cut -f1)"
else
    echo "❌ Error en backup Redis"
fi

# Limpiar backups antiguos (mantener solo los últimos 7 días)
echo "🧹 Limpiando backups antiguos..."
find "$BACKUP_DIR" -name "postgres_backup_*.sql" -mtime +7 -delete
find "$BACKUP_DIR" -name "redis_backup_*.rdb" -mtime +7 -delete

echo "✅ Backup completado exitosamente"
echo "==================================================" 