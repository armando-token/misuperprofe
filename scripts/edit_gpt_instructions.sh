#!/bin/bash

# Script para editar custom_gpt_instructions.md con verificación automática del límite
# Límite máximo: 8000 caracteres

FILE_PATH="memory13/custom_gpt_instructions.md"
MAX_CHARS=8000
BACKUP_DIR="memory13/backups"

echo "🔧 Editor de custom_gpt_instructions.md con verificación de límite"
echo "=================================================="

# Crear directorio de backups si no existe
mkdir -p "$BACKUP_DIR"

# Verificar si el archivo existe
if [ ! -f "$FILE_PATH" ]; then
    echo "❌ ERROR: El archivo $FILE_PATH no existe"
    exit 1
fi

# Crear backup antes de editar
BACKUP_FILE="$BACKUP_DIR/custom_gpt_instructions_$(date +%Y%m%d_%H%M%S).md"
cp "$FILE_PATH" "$BACKUP_FILE"
echo "✅ Backup creado: $BACKUP_FILE"

# Mostrar estadísticas actuales
echo ""
echo "📊 ESTADO ACTUAL:"
CHAR_COUNT=$(wc -c < "$FILE_PATH")
CHAR_COUNT=${CHAR_COUNT// /}
REMAINING=$((MAX_CHARS - CHAR_COUNT))
echo "   Caracteres actuales: $CHAR_COUNT"
echo "   Límite máximo: $MAX_CHARS"
echo "   Caracteres restantes: $REMAINING"
echo "   Porcentaje usado: $((CHAR_COUNT * 100 / MAX_CHARS))%"

echo ""
echo "💡 INSTRUCCIONES:"
echo "   1. El archivo se abrirá en tu editor predeterminado"
echo "   2. Realiza tus cambios"
echo "   3. Guarda el archivo"
echo "   4. El script verificará automáticamente el límite"
echo "   5. Si excede el límite, se restaurará el backup"
echo ""
echo "⚠️  ADVERTENCIA: Si excedes los $MAX_CHARS caracteres, el archivo será rechazado"
echo ""

# Preguntar si continuar
read -p "¿Continuar con la edición? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Edición cancelada"
    exit 0
fi

# Abrir archivo en editor
if command -v nano &> /dev/null; then
    nano "$FILE_PATH"
elif command -v vim &> /dev/null; then
    vim "$FILE_PATH"
elif command -v vi &> /dev/null; then
    vi "$FILE_PATH"
else
    echo "❌ ERROR: No se encontró un editor de texto disponible"
    echo "   Instala nano, vim o vi"
    exit 1
fi

echo ""
echo "🔍 Verificando límite después de la edición..."

# Verificar límite después de editar
NEW_CHAR_COUNT=$(wc -c < "$FILE_PATH")
NEW_CHAR_COUNT=${NEW_CHAR_COUNT// /}

echo "📊 ESTADO DESPUÉS DE LA EDICIÓN:"
echo "   Caracteres actuales: $NEW_CHAR_COUNT"
echo "   Límite máximo: $MAX_CHARS"

if [ "$NEW_CHAR_COUNT" -gt "$MAX_CHARS" ]; then
    EXCESS=$((NEW_CHAR_COUNT - MAX_CHARS))
    echo "❌ PROBLEMA: El archivo excede el límite por $EXCESS caracteres"
    echo "   Restaurando backup..."
    cp "$BACKUP_FILE" "$FILE_PATH"
    echo "✅ Backup restaurado. El archivo original se mantiene."
    echo ""
    echo "💡 SUGERENCIAS PARA REDUCIR $EXCESS caracteres:"
    echo "   1. Eliminar secciones duplicadas"
    echo "   2. Simplificar descripciones"
    echo "   3. Consolidar reglas similares"
    echo "   4. Remover ejemplos redundantes"
    echo "   5. Acortar instrucciones verbosas"
    exit 1
else
    REMAINING=$((MAX_CHARS - NEW_CHAR_COUNT))
    echo "✅ ÉXITO: El archivo está dentro del límite"
    echo "   Caracteres restantes: $REMAINING"
    echo "   Porcentaje usado: $((NEW_CHAR_COUNT * 100 / MAX_CHARS))%"
    echo ""
    echo "🎉 Archivo guardado exitosamente"
fi

echo "==================================================" 