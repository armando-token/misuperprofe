#!/bin/bash

# Script para configurar sincronización automática de XP
# Este script configura un cron job que ejecuta sync_xp_from_attempts.py cada hora

echo "🔄 Configurando sincronización automática de XP..."

# Crear el directorio de logs si no existe
mkdir -p /home/ubuntu/logs

# Crear el cron job para sincronizar XP cada hora
(crontab -l 2>/dev/null; echo "0 * * * * docker exec misuperapi python3 /app/scripts/sync_xp_from_attempts.py >> /home/ubuntu/logs/xp_sync.log 2>&1") | crontab -

echo "✅ Cron job configurado para sincronizar XP cada hora"
echo "📋 Logs disponibles en: /home/ubuntu/logs/xp_sync.log"
echo "🔍 Para verificar: crontab -l"
echo "📊 Para monitorear: tail -f /home/ubuntu/logs/xp_sync.log" 