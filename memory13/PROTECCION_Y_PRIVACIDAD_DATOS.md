# 🛡️ PROTECCIÓN Y PRIVACIDAD DE DATOS - MiSuperProfe

**Effective Date:** July 20, 2025

---

## 📋 **ÍNDICE**

1. [Protección Técnica de Datos](#protección-técnica-de-datos)
2. [Política de Privacidad](#política-de-privacidad)
3. [Derechos del Usuario](#derechos-del-usuario)
4. [Seguridad y Cumplimiento](#seguridad-y-cumplimiento)

---

## 🛡️ **PROTECCIÓN TÉCNICA DE DATOS**

### **🎯 PROBLEMA RESUELTO**

Durante el desarrollo, los reinicios del servidor pueden causar pérdida de datos. Esta documentación explica cómo proteger los datos de los usuarios.

### **📋 SOLUCIONES IMPLEMENTADAS**

#### **1. Volúmenes Persistentes**
- ✅ **PostgreSQL:** Volumen `postgres_data` persistente
- ✅ **Redis:** Volumen `redis_data` persistente con AOF habilitado
- ✅ **Backups:** Directorio `./backups` para backups automáticos
- ✅ **Logs:** Directorio `./logs` para logs persistentes

#### **2. Scripts de Protección**

##### **🔄 Backup Automático**
```bash
./scripts/backup_database.sh
```
- Crea backup de PostgreSQL y Redis
- Limpia backups antiguos (más de 7 días)
- Se ejecuta automáticamente cada 6 horas

##### **🛡️ Reinicio Seguro**
```bash
./scripts/safe_restart.sh
```
- Hace backup antes del reinicio
- Verifica integridad después del reinicio
- **USAR SIEMPRE ESTE SCRIPT PARA REINICIOS**

##### **📊 Restauración de Datos**
```bash
./scripts/restore_database.sh
```
- Restaura desde el backup más reciente
- Pide confirmación antes de sobrescribir
- Restaura PostgreSQL y Redis

##### **🔍 Monitoreo de Datos**
```bash
./scripts/monitor_data.sh
```
- Verifica integridad de datos
- Monitorea espacio en disco
- Revisa logs de errores

#### **3. Backups Automáticos**
```bash
./scripts/setup_cron.sh
```
- Configura backups cada 6 horas
- Backup diario a medianoche
- Logs en `/home/ubuntu/logs/backup.log`

### **🚀 PROCEDIMIENTO SEGURO PARA DESARROLLO**

#### **Antes de Hacer Cambios:**
1. **Hacer backup manual:**
   ```bash
   ./scripts/backup_database.sh
   ```

2. **Verificar estado actual:**
   ```bash
   ./scripts/monitor_data.sh
   ```

#### **Para Reiniciar el Servidor:**
1. **Usar reinicio seguro:**
   ```bash
   ./scripts/safe_restart.sh
   ```

2. **NUNCA usar `docker-compose down && docker-compose up -d` directamente**

#### **Si Se Pierden Datos:**
1. **Verificar backups disponibles:**
   ```bash
   ls -la backups/
   ```

2. **Restaurar desde backup:**
   ```bash
   ./scripts/restore_database.sh
   ```

### **📊 ESTRUCTURA DE PROTECCIÓN**

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

### **⚠️ COMANDOS PELIGROSOS (EVITAR)**

#### **❌ NO USAR:**
```bash
# Puede perder datos
docker-compose down
docker-compose up -d

# Puede borrar volúmenes
docker-compose down -v
docker volume prune
```

#### **✅ USAR SIEMPRE:**
```bash
# Reinicio seguro con backup
./scripts/safe_restart.sh

# Backup manual antes de cambios
./scripts/backup_database.sh
```

### **🔧 CONFIGURACIÓN INICIAL**

#### **1. Configurar backups automáticos:**
```bash
./scripts/setup_cron.sh
```

#### **2. Crear backup inicial:**
```bash
./scripts/backup_database.sh
```

#### **3. Verificar configuración:**
```bash
./scripts/monitor_data.sh
```

### **📈 MONITOREO CONTINUO**

#### **Verificar estado diario:**
```bash
./scripts/monitor_data.sh
```

#### **Revisar logs de backup:**
```bash
tail -f logs/backup.log
```

#### **Verificar cron jobs:**
```bash
crontab -l
```

### **🆘 EN CASO DE EMERGENCIA**

#### **Si se pierden todos los datos:**
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

#### **Si no hay backups:**
1. **Recrear datos de prueba:**
   ```bash
   ./recreate_test_data.sh
   ```

2. **Configurar backups inmediatamente:**
   ```bash
   ./scripts/setup_cron.sh
   ```

---

## 🔒 **POLÍTICA DE PRIVACIDAD**

### **1. Introducción**

MiSuperProfe ("we," "our," or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, and safeguard your information when you use our educational tutoring service.

### **2. Información que Recopilamos**

#### **2.1 Información que Proporcionas**
- **Educational Data:** Questions you ask, answers you provide, and learning progress
- **Usage Data:** How you interact with our tutoring service
- **Performance Data:** Your quiz results, study patterns, and academic progress

#### **2.2 Información que Recopilamos Automáticamente**
- **Technical Data:** IP address, browser type, device information
- **Usage Analytics:** Time spent on topics, areas of difficulty, learning patterns

### **3. Cómo Usamos tu Información**

#### **3.1 Propósitos Educativos**
- Provide personalized tutoring and explanations
- Generate practice questions tailored to your needs
- Track your learning progress and performance
- Recommend study topics based on your performance

#### **3.2 Mejora del Servicio**
- Analyze usage patterns to improve our service
- Develop new educational features
- Ensure technical functionality and security

### **4. Compartir y Divulgar Datos**

#### **4.1 No Compartimos**
- **Personal Information:** We do not sell, trade, or rent your personal information
- **Educational Data:** Your learning progress is kept private
- **Performance Data:** Your quiz results and study patterns are confidential

#### **4.2 Compartir Limitado**
- **Service Providers:** Only with trusted partners who help us operate our service
- **Legal Requirements:** When required by law or to protect our rights
- **Safety:** To prevent fraud or security threats

---

## 👤 **DERECHOS DEL USUARIO**

### **6.1 Acceso y Control**
- **View Your Data:** Request access to your personal information
- **Correct Data:** Update or correct inaccurate information
- **Delete Data:** Request deletion of your personal information
- **Export Data:** Request a copy of your data in a portable format

### **6.2 Opciones de Exclusión**
- **Marketing Communications:** Opt out of promotional emails
- **Data Collection:** Control what information we collect
- **Analytics:** Opt out of usage analytics

### **7. Privacidad de Menores**

#### **7.1 Protección para Menores**
- **Age Verification:** We do not knowingly collect information from children under 13
- **Parental Consent:** Parental consent required for users under 18
- **Educational Focus:** Our service is designed for educational purposes

### **8. Transferencias Internacionales de Datos**

#### **8.1 Ubicación de Datos**
- **Primary Storage:** Data stored in secure cloud infrastructure
- **Compliance:** We comply with applicable data protection laws
- **Safeguards:** Appropriate safeguards for international data transfers

---

## 🔐 **SEGURIDAD Y CUMPLIMIENTO**

### **5.1 Medidas de Protección**
- **Encryption:** All data is encrypted in transit and at rest
- **Access Controls:** Strict access controls to protect your information
- **Regular Audits:** We regularly review our security practices

### **5.2 Retención de Datos**
- **Educational Data:** Retained for educational purposes and service improvement
- **Account Data:** Retained while your account is active
- **Deletion:** You can request deletion of your data at any time

### **11.1 Cumplimiento GDPR**
- **Consent:** We process data based on your consent
- **Legitimate Interest:** For service improvement and security
- **Educational Purpose:** For providing educational services

### **11.2 Cumplimiento CCPA**
- **California Residents:** Additional rights under CCPA
- **Non-Discrimination:** We do not discriminate based on privacy choices
- **Authorized Agent:** You may designate an authorized agent

### **12. Enfoque Educativo**

#### **12.1 Análisis de Aprendizaje**
- **Purpose:** Improve educational outcomes
- **Anonymization:** Data is anonymized for research purposes
- **Educational Benefit:** All analytics serve educational improvement

#### **12.2 Integridad Académica**
- **Honest Learning:** We promote honest academic practices
- **No Cheating:** Our service is designed for learning, not cheating
- **Educational Support:** We provide legitimate educational support

### **9. Cambios a esta Política**

#### **9.1 Actualizaciones**
- **Notification:** We will notify you of any material changes
- **Review:** We encourage you to review this policy periodically
- **Consent:** Continued use constitutes acceptance of changes

### **10. Información de Contacto**

#### **10.1 Preguntas y Preocupaciones**
- **Email:** privacy@misuperprofe.com
- **Address:** [Your Business Address]
- **Response Time:** We will respond to inquiries within 30 days

---

## 🎯 **RESULTADO FINAL**

### **✅ PROTECCIÓN TÉCNICA:**
- Los datos están protegidos durante reinicios
- Backups automáticos cada 6 horas
- Reinicios seguros con verificación
- Restauración rápida en caso de pérdida
- Monitoreo continuo del estado

### **✅ PRIVACIDAD DEL USUARIO:**
- Cumplimiento GDPR y CCPA
- Enfoque educativo y transparente
- Control total sobre datos personales
- Protección especial para menores
- Encriptación y controles de acceso

**Los usuarios reales no perderán su progreso durante el desarrollo y sus datos están completamente protegidos.**

---

**Last Updated:** July 20, 2025

This combined policy is designed to protect your privacy while enabling us to provide effective educational services. We are committed to transparency and will always inform you of any changes to how we handle your data. 