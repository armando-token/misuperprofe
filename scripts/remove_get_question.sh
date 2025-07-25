#!/bin/bash

# Script para eliminar completamente cualquier referencia a /get_question
# del archivo custom_gpt_instructions.md

FILE_PATH="memory13/custom_gpt_instructions.md"
BACKUP_FILE="memory13/custom_gpt_instructions_backup_$(date +%Y%m%d_%H%M%S).md"

echo "🚨 Eliminando completamente /get_question del archivo..."
echo "=================================================="

# Crear backup
cp "$FILE_PATH" "$BACKUP_FILE"
echo "✅ Backup creado: $BACKUP_FILE"

# Eliminar todas las referencias a /get_question
sed -i '/\/get_question/d' "$FILE_PATH"
sed -i '/get_question/d' "$FILE_PATH"

# Agregar regla absoluta al inicio
sed -i '1a\
## 🚨 **REGLAS ABSOLUTAS - NO IGNORAR:**\
\
**SIEMPRE usa DECO para preguntas. NUNCA uses /get_question:**\
- "dame una pregunta" → `POST /deco/question`\
- "pregunta" → `POST /deco/question`\
- "si" → `POST /deco/question`\
- "otra" → `POST /deco/question`\
- "otra más" → `POST /deco/question`\
- "quiero estudiar [curso]" → `POST /deco/question`\
- "estudiemos [curso]" → `POST /deco/question`\
- **PROHIBIDO:** `/get_question` - NUNCA lo uses\
' "$FILE_PATH"

echo "✅ Todas las referencias a /get_question eliminadas"
echo "✅ Regla absoluta agregada al inicio"

# Verificar resultado
echo ""
echo "📊 Verificando resultado:"
./scripts/check_gpt_instructions_limit.sh

echo ""
echo "🔍 Buscando referencias restantes a get_question:"
grep -i "get_question" "$FILE_PATH" || echo "✅ No se encontraron referencias a get_question"

echo "==================================================" 