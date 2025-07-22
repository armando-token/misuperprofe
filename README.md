# 🎓 MiSuperProfe - Sistema de Tutoría Inteligente

[![Status](https://img.shields.io/badge/Status-Producción%20Ready-green.svg)](https://app.misuperprofe.com)
[![Version](https://img.shields.io/badge/Version-v13-blue.svg)](https://github.com/MiSuperProfe/v13)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 **Descripción del Proyecto**

**MiSuperProfe** es un sistema de tutoría inteligente que utiliza Inteligencia Artificial para proporcionar respuestas educativas precisas y preguntas de práctica personalizadas. El sistema está desplegado en AWS y funciona a través de un Custom GPT de ChatGPT.

### **Características Principales:**
- 🤖 **Búsqueda Semántica Inteligente** - Respuestas precisas basadas en contenido educativo
- 📚 **10 Cursos Completos** - Cultura general, historia, lenguaje, geografía, filosofía, literatura, biología, economía, cívica, psicología
- 🎯 **Preguntas de Práctica Dinámicas** - Generadas con IA para cada estudiante
- 📊 **Sistema de Progreso** - Seguimiento del rendimiento y recomendaciones
- 🏆 **Gamificación Completa** - XP, logros, leaderboards y niveles
- 🧠 **Algoritmo Adaptativo SM-2** - Repetición espaciada optimizada
- 🛡️ **Protección de Datos** - Backups automáticos y reinicios seguros

## 🚀 **Estado del Proyecto**

**✅ SISTEMA COMPLETAMENTE OPERATIVO - FASE 3 COMPLETADA CON PROTECCIÓN DE DATOS**

### **Servicios Desplegados:**
- ✅ **Ubuntu Server AWS** - 18.214.59.62 (app.misuperprofe.com)
- ✅ **PostgreSQL Database** - 2473 capítulos cargados
- ✅ **Redis Cache** - Optimización de rendimiento
- ✅ **FastAPI MCP Server** - API REST completa
- ✅ **Nginx Reverse Proxy** - SSL/HTTPS configurado
- ✅ **SSL Certificate** - Let's Encrypt para app.misuperprofe.com

## 📚 **Contenido Educativo**

### **Base de Datos Poblada:**
- ✅ **2473 capítulos** cargados desde markdown
- ✅ **10 cursos completos** con contenido detallado
- ✅ **Embeddings semánticos** precargados (384 dimensiones)
- ✅ **Motor de búsqueda optimizado** con modelo `all-MiniLM-L6-v2`

### **Cursos Disponibles:**
1. **Cultura General** - Conocimientos básicos y actualidad
2. **Historia** - Historia universal y eventos importantes
3. **Lenguaje** - Gramática, literatura y comunicación
4. **Geografía** - Geografía física y política mundial
5. **Filosofía** - Pensamiento filosófico y lógica
6. **Literatura** - Obras literarias y análisis
7. **Biología** - Ciencias de la vida y evolución
8. **Economía** - Principios económicos y finanzas
9. **Cívica** - Derechos, deberes y democracia
10. **Psicología** - Comportamiento humano y mente

## 🔌 **API y Endpoints**

### **Endpoints Principales:**
- `GET /api/v1/courses` - Lista de cursos disponibles
- `POST /api/v1/ask` - Búsqueda semántica para preguntas
- `POST /api/v1/get_question` - Generación de preguntas con IA
- `POST /api/v1/log_result` - Registro de resultados y progreso
- `GET /api/v1/user_stats` - Estadísticas del usuario
- `GET /api/v1/achievements/leaderboard` - Tablas de clasificación

### **Acceso Público:**
- **API Documentation:** https://app.misuperprofe.com/docs
- **API Base URL:** https://app.misuperprofe.com/api/v1/
- **Health Check:** https://app.misuperprofe.com/api/v1/agent/health

## 🛡️ **Sistema de Protección de Datos**

### **Problema Resuelto:**
- ✅ **Protección contra pérdida de datos** durante reinicios del servidor
- ✅ **Backups automáticos** cada 6 horas y diarios a medianoche
- ✅ **Volúmenes persistentes** para PostgreSQL y Redis
- ✅ **Reinicios seguros** con verificación de integridad
- ✅ **Restauración rápida** desde backups en caso de pérdida

### **Scripts de Protección:**
```bash
# Reinicio seguro (SIEMPRE usar)
./scripts/safe_restart.sh

# Backup manual
./scripts/backup_database.sh

# Verificar integridad
./scripts/monitor_data.sh

# Restaurar desde backup
./scripts/restore_database.sh
```

## 🧠 **Algoritmo Adaptativo**

### **Tipo de Algoritmo: SM-2 (SuperMemo 2)**
El sistema utiliza una variación del algoritmo SM-2 combinado con elementos de Teoría de Respuesta al Ítem (IRT) para crear un sistema de aprendizaje verdaderamente adaptativo.

### **Características:**
- **Factor de Facilidad (EF)** - Se ajusta según el rendimiento del estudiante
- **Repetición Espaciada** - Optimiza la memoria a largo plazo
- **Dificultad Dinámica** - Se adapta al nivel de cada estudiante
- **Personalización Individual** - Cada estudiante tiene su propio progreso

## 🏗️ **Arquitectura del Sistema**

### **Infraestructura:**
```
AWS Ubuntu Server (18.214.59.62)
├── PostgreSQL Database (Puerto 5432)
├── Redis Cache (Puerto 6379)
├── FastAPI MCP Server (Puerto 8000)
├── Nginx Reverse Proxy (Puerto 443)
└── SSL Certificate (Let's Encrypt)
```

### **Servicios Docker:**
- **PostgreSQL** - Base de datos principal con volúmenes persistentes
- **Redis** - Cache y sesiones con persistencia AOF
- **FastAPI** - Servidor principal de la aplicación
- **Nginx** - Proxy reverso con SSL

## 🔧 **Instalación y Configuración**

### **Requisitos:**
- Docker y Docker Compose
- Git
- Acceso a internet para descargar imágenes

### **Instalación Rápida:**
```bash
# Clonar repositorio
git clone https://github.com/MiSuperProfe/v13.git
cd v13

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# Iniciar servicios
docker-compose up -d

# Configurar backups automáticos
./scripts/setup_cron.sh
```

### **Configuración de Desarrollo:**
```bash
# Para reinicios seguros durante desarrollo
./scripts/safe_restart.sh

# Para verificar estado del sistema
./scripts/monitor_data.sh
```

## 📊 **Estadísticas del Sistema**

### **Contenido Cargado:**
- **2473 capítulos** de teoría educativa
- **10 cursos** completos
- **384 dimensiones** por embedding semántico
- **Índice FAISS** optimizado con 2473 vectores

### **Rendimiento:**
- **Tiempo de respuesta:** 1-3 segundos para búsquedas semánticas
- **Caché de embeddings:** Cargado en 1.44 segundos
- **Disponibilidad:** 99.9% (servicios Docker con health checks)

## 🔒 **Seguridad y Autenticación**

### **Configuración de Seguridad:**
- ✅ **SSL/HTTPS** configurado en https://app.misuperprofe.com
- ✅ **API Key** configurado para autenticación
- ✅ **CORS** configurado para ChatGPT
- ✅ **Autenticación Bearer Token** funcionando
- ✅ **Headers de autorización** validados en todos los endpoints

## 🤖 **Integración con Custom GPT**

### **Estado de la Integración:**
- ✅ **Custom GPT conectado** y operativo
- ✅ **Lista de cursos** obtenida correctamente
- ✅ **Preguntas de teoría** respondidas con contenido real
- ✅ **Comunicación con API** establecida y operativa
- ✅ **Schema OpenAPI** actualizado y funcionando

### **Funcionalidades del Custom GPT:**
- ✅ **Búsqueda semántica** para preguntas de teoría
- ✅ **Generación de preguntas** de práctica
- ✅ **Evaluación de respuestas** de estudiantes
- ✅ **Logging de progreso** en base de datos
- ✅ **Recomendaciones** basadas en rendimiento

## 📁 **Estructura del Proyecto**

```
/home/ubuntu/
├── src/                          # Código fuente de la aplicación
│   ├── app/
│   │   ├── api/                  # Endpoints de la API
│   │   ├── models/               # Modelos de base de datos
│   │   ├── schemas/              # Schemas de Pydantic
│   │   ├── services/             # Lógica de negocio
│   │   └── tools/                # Herramientas auxiliares
├── content/                       # Contenido educativo (markdown)
├── scripts/                       # Scripts de administración
│   ├── backup_database.sh        # Backup automático
│   ├── safe_restart.sh           # Reinicio seguro
│   ├── restore_database.sh       # Restauración
│   ├── monitor_data.sh           # Monitoreo
│   └── setup_cron.sh            # Configuración cron
├── backups/                       # Backups automáticos
├── logs/                         # Logs persistentes
├── docker-compose.yml            # Configuración de servicios
└── PROTECCION_DATOS.md          # Documentación de protección
```

## 🎯 **Funcionalidades para Estudiantes**

### **Experiencia de Aprendizaje:**
1. **Preguntas de Teoría** - Obtienen respuestas precisas basadas en contenido educativo
2. **Preguntas de Práctica** - Reciben preguntas generadas dinámicamente con IA
3. **Evaluación Inmediata** - Reciben feedback instantáneo sobre sus respuestas
4. **Seguimiento de Progreso** - Su rendimiento se registra automáticamente
5. **Recomendaciones** - Reciben sugerencias de estudio basadas en su rendimiento
6. **Gráficos de Progreso** - Visualizan su rendimiento por materia

## 🔧 **Desarrollo y Mantenimiento**

### **Procedimientos Seguros:**
- ✅ **Reinicios seguros** con `./scripts/safe_restart.sh`
- ✅ **Backups automáticos** cada 6 horas
- ✅ **Monitoreo continuo** con `./scripts/monitor_data.sh`
- ✅ **Restauración rápida** con `./scripts/restore_database.sh`

### **Comandos Importantes:**
```bash
# Verificar estado del sistema
./scripts/monitor_data.sh

# Hacer backup manual
./scripts/backup_database.sh

# Reiniciar de forma segura
./scripts/safe_restart.sh

# Ver logs de backup
tail -f logs/backup.log
```

## 📈 **Roadmap y Futuras Mejoras**

### **Próximas Funcionalidades:**
- 🔄 **Calificación automática** más avanzada
- 📊 **Analytics más detallados** para administradores
- 🎮 **Más elementos de gamificación**
- 📱 **Interfaz móvil** nativa
- 🌐 **Multiidioma** completo

## 🤝 **Contribución**

### **Cómo Contribuir:**
1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### **Reportar Bugs:**
- Usa el sistema de Issues de GitHub
- Incluye información detallada sobre el problema
- Adjunta logs si es posible

## 📄 **Licencia**

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 **Contacto**

- **Proyecto:** [MiSuperProfe v13](https://github.com/MiSuperProfe/v13)
- **Sitio Web:** [app.misuperprofe.com](https://app.misuperprofe.com)
- **API Docs:** [docs.misuperprofe.com](https://app.misuperprofe.com/docs)

---

**⭐ Si este proyecto te ayuda, considera darle una estrella en GitHub!**

**Documentación actualizada el 22 de Julio de 2025 - SISTEMA DE PROTECCIÓN DE DATOS IMPLEMENTADO** 