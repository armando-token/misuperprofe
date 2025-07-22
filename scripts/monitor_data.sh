#!/bin/bash

# Script de monitoreo de datos para MiSuperProfe
# Este script verifica la integridad de los datos

echo "🔍 MONITOREO DE DATOS - $(date)"
echo "=================================================="

# Verificar conectividad de servicios
echo "🔍 Verificando servicios..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Servicios funcionando"
else
    echo "❌ Servicios no funcionando"
    exit 1
fi

# Verificar base de datos
echo "📊 Verificando base de datos..."
DB_COUNT=$(docker-compose exec -T db psql -U mysuper_user -d mysuper_bd -t -c "SELECT COUNT(*) FROM attempts;" 2>/dev/null | tr -d ' ')
if [ "$DB_COUNT" -gt 0 ]; then
    echo "✅ Base de datos: $DB_COUNT registros de intentos"
else
    echo "⚠️  Base de datos: Sin registros de intentos"
fi

# Verificar Redis
echo "📊 Verificando Redis..."
REDIS_KEYS=$(docker-compose exec -T redis redis-cli DBSIZE 2>/dev/null)
if [ "$REDIS_KEYS" -gt 0 ]; then
    echo "✅ Redis: $REDIS_KEYS claves activas"
else
    echo "⚠️  Redis: Sin claves activas"
fi

# Verificar backups
echo "📁 Verificando backups..."
BACKUP_COUNT=$(ls /home/ubuntu/backups/postgres_backup_*.sql 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt 0 ]; then
    LATEST_BACKUP=$(ls -t /home/ubuntu/backups/postgres_backup_*.sql | head -1)
    BACKUP_AGE=$(($(date +%s) - $(stat -c %Y "$LATEST_BACKUP")))
    BACKUP_HOURS=$((BACKUP_AGE / 3600))
    echo "✅ Backups: $BACKUP_COUNT disponibles (último hace $BACKUP_HOURS horas)"
else
    echo "❌ Backups: No se encontraron backups"
fi

# Verificar espacio en disco
echo "💾 Verificando espacio en disco..."
DISK_USAGE=$(df /home/ubuntu | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo "✅ Espacio en disco: ${DISK_USAGE}% usado"
else
    echo "⚠️  Espacio en disco: ${DISK_USAGE}% usado (alto)"
fi

# Verificar logs de errores
echo "📋 Verificando logs..."
ERROR_COUNT=$(docker-compose logs --tail=100 | grep -i error | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo "✅ Logs: Sin errores recientes"
else
    echo "⚠️  Logs: $ERROR_COUNT errores recientes"
fi

echo "✅ Monitoreo completado"
echo "==================================================" 