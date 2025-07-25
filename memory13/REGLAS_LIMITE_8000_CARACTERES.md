# REGLAS PARA MANTENER LÍMITE DE 8000 CARACTERES

## 🎯 **LÍMITE CRÍTICO: 8000 CARACTERES**

El archivo `memory13/custom_gpt_instructions.md` **NUNCA debe exceder 8000 caracteres** porque:
- ChatGPT rechaza archivos que excedan este límite
- El archivo se vuelve inutilizable
- Se pierden todas las instrucciones

## 🔧 **HERRAMIENTAS DISPONIBLES:**

### **1. Script de Verificación:**
```bash
./scripts/check_gpt_instructions_limit.sh
```
- Verifica automáticamente el límite
- Muestra estadísticas detalladas
- Sugiere acciones si excede el límite

### **2. Editor Seguro:**
```bash
./scripts/edit_gpt_instructions.sh
```
- Crea backup automático antes de editar
- Verifica límite después de editar
- Restaura backup si excede el límite

### **3. Verificación Previa:**
```bash
./scripts/pre_edit_check.sh
```
- Verifica límite antes de editar
- Previene problemas

## 📋 **REGLAS OBLIGATORIAS:**

### **✅ ANTES DE EDITAR:**
1. **SIEMPRE ejecuta:** `./scripts/check_gpt_instructions_limit.sh`
2. **Verifica caracteres restantes** antes de agregar contenido
3. **Calcula espacio disponible** antes de agregar nuevas secciones

### **✅ DURANTE LA EDICIÓN:**
1. **Elimina contenido redundante** antes de agregar nuevo
2. **Consolida secciones similares** en lugar de duplicar
3. **Simplifica descripciones** manteniendo claridad
4. **Usa abreviaciones** cuando sea posible
5. **Prioriza contenido esencial** sobre ejemplos extensos

### **✅ DESPUÉS DE EDITAR:**
1. **SIEMPRE ejecuta:** `./scripts/check_gpt_instructions_limit.sh`
2. **Verifica que esté dentro del límite**
3. **Si excede, reduce inmediatamente**

## 🚨 **CONTENIDO QUE SE PUEDE ELIMINAR:**

### **❌ ELIMINAR SIEMPRE:**
- Secciones duplicadas
- Ejemplos redundantes
- Descripciones verbosas
- Instrucciones repetitivas
- Comentarios extensos
- Formato excesivo (emojis, decoraciones)

### **✅ MANTENER SIEMPRE:**
- Endpoints principales
- Reglas críticas (DECO, user_id)
- Configuración HTTP
- Flujos de interacción esenciales
- Comportamiento esperado

## 📊 **ESTRATEGIAS DE OPTIMIZACIÓN:**

### **1. Consolidación:**
```markdown
# ANTES (redundante):
- "pregunta de [curso]" → `POST /deco/question`
- "dame pregunta de [curso]" → `POST /deco/question`
- "quiero pregunta de [curso]" → `POST /deco/question`

# DESPUÉS (consolidado):
- "pregunta de [curso]" → `POST /deco/question`
```

### **2. Simplificación:**
```markdown
# ANTES (verboso):
- "Pregunta tipo UNMSM 2025 con contexto realista y habilidades cognitivas" → `POST /deco/question`

# DESPUÉS (simplificado):
- "Pregunta tipo UNMSM" → `POST /deco/question`
```

### **3. Eliminación de Duplicados:**
```markdown
# ELIMINAR secciones duplicadas como:
## 🎯 PRIORIDAD DECO (aparece 2 veces)
## 🔍 INTERPRETACIÓN DINÁMICA (redundante)
```

## 🎯 **PRIORIDADES DE CONTENIDO:**

### **🔥 CRÍTICO (mantener siempre):**
1. Configuración HTTP
2. User_id correcto
3. Prioridad DECO
4. Endpoints principales
5. Reglas críticas

### **📈 IMPORTANTE (mantener si hay espacio):**
1. Ejemplos específicos
2. Flujos detallados
3. Comportamiento esperado
4. Casos de uso

### **💡 OPCIONAL (eliminar si es necesario):**
1. Descripciones extensas
2. Ejemplos múltiples
3. Formato decorativo
4. Comentarios explicativos

## ⚡ **COMANDOS ÚTILES:**

### **Verificar límite:**
```bash
./scripts/check_gpt_instructions_limit.sh
```

### **Editar con seguridad:**
```bash
./scripts/edit_gpt_instructions.sh
```

### **Contar caracteres manualmente:**
```bash
wc -c memory13/custom_gpt_instructions.md
```

### **Ver porcentaje usado:**
```bash
CHAR_COUNT=$(wc -c < memory13/custom_gpt_instructions.md)
echo "Porcentaje usado: $((CHAR_COUNT * 100 / 8000))%"
```

## 🚨 **ADVERTENCIAS:**

### **❌ NUNCA HAGAS:**
- Agregar contenido sin verificar límite
- Ignorar advertencias de exceso
- Duplicar secciones existentes
- Usar formato excesivo
- Agregar ejemplos redundantes

### **✅ SIEMPRE HAGAS:**
- Verificar límite antes de editar
- Eliminar contenido redundante
- Consolidar secciones similares
- Simplificar descripciones
- Priorizar contenido esencial

## 📈 **META DE OPTIMIZACIÓN:**

- **Objetivo:** Mantener archivo entre 7000-7500 caracteres
- **Reserva:** 500-1000 caracteres para futuras ediciones
- **Máximo:** NUNCA exceder 8000 caracteres

**Documentación actualizada el 23 de Julio de 2025 - REGLAS PARA MANTENER LÍMITE DE 8000 CARACTERES** 