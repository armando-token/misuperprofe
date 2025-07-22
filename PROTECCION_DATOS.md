# 🛡️ PROTECCIÓN DE DATOS - MiSuperProfe

## 🎯 **PROBLEMA RESUELTO**

Durante el desarrollo, los reinicios del servidor pueden causar pérdida de datos. Esta documentación explica cómo proteger los datos de los usuarios.

## 📋 **SOLUCIONES IMPLEMENTADAS**

### **1. Volúmenes Persistentes**
- ✅ **PostgreSQL:** Volumen `postgres_data` persistente
- ✅ **Redis:** Volumen `redis_data` persistente con AOF habilitado
- ✅ **Backups:** Directorio `./backups` para backups automáticos
- ✅ **Logs:** Directorio `./logs` para logs persistentes

### **2. Scripts de Protección**

#### **🔄 Backup Automático**
```bash
./scripts/backup_database.sh
```
- Crea backup de PostgreSQL y Redis
- Limpia backups antiguos (más de 7 días)
- Se ejecuta automáticamente cada 6 horas

#### **🛡️ Reinicio Seguro**
```bash
./scripts/safe_restart.sh
```
- Hace backup antes del reinicio
- Verifica integridad después del reinicio
- **USAR SIEMPRE ESTE SCRIPT PARA REINICIOS**

#### **📊 Restauración de Datos**
```bash
./scripts/restore_database.sh
```
- Restaura desde el backup más reciente
- Pide confirmación antes de sobrescribir
- Restaura PostgreSQL y Redis

#### **🔍 Monitoreo de Datos**
```bash
./scripts/monitor_data.sh
```
- Verifica integridad de datos
- Monitorea espacio en disco
- Revisa logs de errores

### **3. Backups Automáticos**
```bash
./scripts/setup_cron.sh
```
- Configura backups cada 6 horas
- Backup diario a medianoche
- Logs en `/home/ubuntu/logs/backup.log`

## 🚀 **PROCEDIMIENTO SEGURO PARA DESARROLLO**

### **Antes de Hacer Cambios:**
1. **Hacer backup manual:**
   ```bash
   ./scripts/backup_database.sh
   ```

2. **Verificar estado actual:**
   ```bash
   ./scripts/monitor_data.sh
   ```

### **Para Reiniciar el Servidor:**
1. **Usar reinicio seguro:**
   ```bash
   ./scripts/safe_restart.sh
   ```

2. **NUNCA usar `docker-compose down && docker-compose up -d` directamente**

### **Si Se Pierden Datos:**
1. **Verificar backups disponibles:**
   ```bash
   ls -la backups/
   ```

2. **Restaurar desde backup:**
   ```bash
   ./scripts/restore_database.sh
   ```

## 📊 **ESTRUCTURA DE PROTECCIÓN**

```
/home/ubuntu/
├── backups/                    # Backups automáticos
│   ├── postgres_backup_*.sql   # Backups PostgreSQL
│   └── redis_backup_*.rdb      # Backups Redis
├── logs/                       # Logs persistentes
│   └── backup.log             # Logs de backups
├── scripts/                    # Scripts de protección
│   ├── backup_database.sh     # Backup automático
│   ├── safe_restart.sh        # Reinicio seguro
│   ├── restore_database.sh    # Restauración
│   ├── monitor_data.sh        # Monitoreo
│   └── setup_cron.sh         # Configuración cron
└── docker-compose.yml         # Volúmenes persistentes
```

## ⚠️ **COMANDOS PELIGROSOS (EVITAR)**

### **❌ NO USAR:**
```bash
# Puede perder datos
docker-compose down
docker-compose up -d

# Puede borrar volúmenes
docker-compose down -v
docker volume prune
```

### **✅ USAR SIEMPRE:**
```bash
# Reinicio seguro con backup
./scripts/safe_restart.sh

# Backup manual antes de cambios
./scripts/backup_database.sh
```

## 🔧 **CONFIGURACIÓN INICIAL**

### **1. Configurar backups automáticos:**
```bash
./scripts/setup_cron.sh
```

### **2. Crear backup inicial:**
```bash
./scripts/backup_database.sh
```

### **3. Verificar configuración:**
```bash
./scripts/monitor_data.sh
```

## 📈 **MONITOREO CONTINUO**

### **Verificar estado diario:**
```bash
./scripts/monitor_data.sh
```

### **Revisar logs de backup:**
```bash
tail -f logs/backup.log
```

### **Verificar cron jobs:**
```bash
crontab -l
```

## 🆘 **EN CASO DE EMERGENCIA**

### **Si se pierden todos los datos:**
1. **Buscar backups:**
   ```bash
   ls -la backups/
   ```

2. **Restaurar último backup:**
   ```bash
   ./scripts/restore_database.sh
   ```

3. **Verificar restauración:**
   ```bash
   ./scripts/monitor_data.sh
   ```

### **Si no hay backups:**
1. **Recrear datos de prueba:**
   ```bash
   ./recreate_test_data.sh
   ```

2. **Configurar backups inmediatamente:**
   ```bash
   ./scripts/setup_cron.sh
   ```

## 🎯 **RESULTADO**

Con esta configuración:
- ✅ **Los datos están protegidos** durante reinicios
- ✅ **Backups automáticos** cada 6 horas
- ✅ **Reinicios seguros** con verificación
- ✅ **Restauración rápida** en caso de pérdida
- ✅ **Monitoreo continuo** del estado

**Los usuarios reales no perderán su progreso durante el desarrollo.** 