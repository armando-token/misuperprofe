#!/bin/bash

# Script de reinicio seguro para MiSuperProfe
# Este script hace backup antes de reiniciar para proteger los datos

echo "🛡️ REINICIO SEGURO - $(date)"
echo "=================================================="

# Hacer backup antes del reinicio
echo "📊 Creando backup antes del reinicio..."
./scripts/backup_database.sh

if [ $? -ne 0 ]; then
    echo "❌ Error en backup. ¿Continuar con el reinicio? (y/n): "
    read -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Reinicio cancelado"
        exit 1
    fi
fi

# Reiniciar servicios
echo "🔄 Reiniciando servicios..."
docker-compose down
docker-compose up -d

# Esperar a que los servicios estén listos
echo "⏳ Esperando a que los servicios estén listos..."
sleep 30

# Verificar que los servicios estén funcionando
echo "🔍 Verificando servicios..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Servicios reiniciados exitosamente"
else
    echo "❌ Error en el reinicio de servicios"
    exit 1
fi

# Verificar conectividad de la base de datos
echo "🔍 Verificando conectividad de la base de datos..."
if docker-compose exec -T db pg_isready -U mysuper_user -d mysuper_bd; then
    echo "✅ Base de datos conectada"
else
    echo "❌ Error en la conexión a la base de datos"
    exit 1
fi

# Verificar que los datos estén intactos
echo "🔍 Verificando integridad de datos..."
USER_COUNT=$(docker-compose exec -T db psql -U mysuper_user -d mysuper_bd -t -c "SELECT COUNT(*) FROM attempts;" 2>/dev/null | tr -d ' ')
if [ "$USER_COUNT" -gt 0 ]; then
    echo "✅ Datos verificados: $USER_COUNT registros encontrados"
else
    echo "⚠️  Advertencia: No se encontraron registros de intentos"
fi

echo "✅ Reinicio seguro completado"
echo "==================================================" 