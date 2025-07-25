#!/bin/bash

# Script para verificar el límite de caracteres en custom_gpt_instructions.md
# Límite máximo: 8000 caracteres

FILE_PATH="memory13/custom_gpt_instructions.md"
MAX_CHARS=8000

echo "🔍 Verificando límite de caracteres en custom_gpt_instructions.md..."
echo "=================================================="

# Verificar si el archivo existe
if [ ! -f "$FILE_PATH" ]; then
    echo "❌ ERROR: El archivo $FILE_PATH no existe"
    exit 1
fi

# Contar caracteres
CHAR_COUNT=$(wc -c < "$FILE_PATH")
CHAR_COUNT=${CHAR_COUNT// /}  # Eliminar espacios

echo "📊 Estadísticas del archivo:"
echo "   Archivo: $FILE_PATH"
echo "   Caracteres actuales: $CHAR_COUNT"
echo "   Límite máximo: $MAX_CHARS"

# Calcular diferencia
if [ "$CHAR_COUNT" -gt "$MAX_CHARS" ]; then
    EXCESS=$((CHAR_COUNT - MAX_CHARS))
    echo "❌ PROBLEMA: El archivo excede el límite por $EXCESS caracteres"
    echo "   Necesitas reducir $EXCESS caracteres"
    echo ""
    echo "💡 SUGERENCIAS PARA REDUCIR:"
    echo "   1. Eliminar secciones duplicadas"
    echo "   2. Simplificar descripciones"
    echo "   3. Consolidar reglas similares"
    echo "   4. Remover ejemplos redundantes"
    echo "   5. Acortar instrucciones verbosas"
    exit 1
else
    REMAINING=$((MAX_CHARS - CHAR_COUNT))
    echo "✅ ÉXITO: El archivo está dentro del límite"
    echo "   Caracteres restantes: $REMAINING"
    echo "   Porcentaje usado: $((CHAR_COUNT * 100 / MAX_CHARS))%"
fi

echo "==================================================" 