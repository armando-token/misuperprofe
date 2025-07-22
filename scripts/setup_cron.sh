#!/bin/bash

# Script para configurar backups automáticos con cron

echo "⏰ CONFIGURANDO BACKUPS AUTOMÁTICOS"
echo "=================================================="

# Crear directorio de scripts si no existe
mkdir -p /home/ubuntu/scripts

# Hacer ejecutables los scripts
chmod +x /home/ubuntu/scripts/backup_database.sh
chmod +x /home/ubuntu/scripts/safe_restart.sh
chmod +x /home/ubuntu/scripts/restore_database.sh

# Crear backup inicial
echo "📊 Creando backup inicial..."
./scripts/backup_database.sh

# Configurar cron jobs
echo "⏰ Configurando cron jobs..."

# Backup cada 6 horas
(crontab -l 2>/dev/null; echo "0 */6 * * * /home/ubuntu/scripts/backup_database.sh >> /home/ubuntu/logs/backup.log 2>&1") | crontab -

# Backup antes de medianoche
(crontab -l 2>/dev/null; echo "0 0 * * * /home/ubuntu/scripts/backup_database.sh >> /home/ubuntu/logs/backup.log 2>&1") | crontab -

# Verificar que se configuró correctamente
echo "📋 Cron jobs configurados:"
crontab -l

echo "✅ Backups automáticos configurados"
echo "   - Backup cada 6 horas"
echo "   - Backup diario a medianoche"
echo "   - Logs en /home/ubuntu/logs/backup.log"
echo "==================================================" 