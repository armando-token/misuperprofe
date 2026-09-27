#!/bin/bash

# Script de restauración para MiSuperProfe
# Este script restaura los datos desde un backup

BACKUP_DIR="${BACKUP_DIR:-/home/ubuntu/backups}"
DB_NAME="${POSTGRES_DB:-mysuper_bd}"
DB_USER="${POSTGRES_USER:-mysuper_user}"

echo "🔄 SCRIPT DE RESTAURACIÓN - $(date)"
echo "=================================================="

# Listar backups disponibles
echo "📁 Backups disponibles:"
echo "----------------------------------------"
ls -la "$BACKUP_DIR"/*.sql 2>/dev/null | head -10

if [ $? -ne 0 ]; then
    echo "❌ No se encontraron backups de PostgreSQL"
    exit 1
fi

# Seleccionar backup más reciente
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/postgres_backup_*.sql 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "❌ No se encontraron backups"
    exit 1
fi

echo "📊 Restaurando desde: $LATEST_BACKUP"
echo "   Tamaño: $(du -h "$LATEST_BACKUP" | cut -f1)"

# Confirmar restauración
read -p "¿Estás seguro de que quieres restaurar? Esto sobrescribirá los datos actuales (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Restauración cancelada"
    exit 1
fi

# Detener servicios
echo "🛑 Deteniendo servicios..."
docker-compose down

# Restaurar PostgreSQL
echo "📊 Restaurando PostgreSQL..."
docker-compose up -d db
sleep 10  # Esperar a que PostgreSQL esté listo

docker-compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker-compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" < "$LATEST_BACKUP"

if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL restaurado exitosamente"
else
    echo "❌ Error en restauración de PostgreSQL"
    exit 1
fi

# Restaurar Redis (opcional)
LATEST_REDIS_BACKUP=$(ls -t "$BACKUP_DIR"/redis_backup_*.rdb 2>/dev/null | head -1)

if [ -n "$LATEST_REDIS_BACKUP" ]; then
    echo "📊 Restaurando Redis..."
    docker-compose up -d redis
    sleep 5
    
    docker cp "$LATEST_REDIS_BACKUP" misuperredis:/data/dump.rdb
    docker-compose exec redis redis-cli FLUSHALL
    docker-compose exec redis redis-cli BGREWRITEAOF
    
    echo "✅ Redis restaurado exitosamente"
fi

# Reiniciar servicios
echo "🚀 Reiniciando servicios..."
docker-compose up -d

echo "✅ Restauración completada exitosamente"
echo "==================================================" 