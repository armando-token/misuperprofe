#!/bin/bash

# Script que se ejecuta automáticamente antes de editar custom_gpt_instructions.md
# Verifica el límite de caracteres y previene exceder los 8000 caracteres

FILE_PATH="memory13/custom_gpt_instructions.md"
MAX_CHARS=8000

# Función para verificar límite
check_limit() {
    if [ ! -f "$FILE_PATH" ]; then
        echo "❌ ERROR: El archivo $FILE_PATH no existe"
        return 1
    fi
    
    CHAR_COUNT=$(wc -c < "$FILE_PATH")
    CHAR_COUNT=${CHAR_COUNT// /}
    
    if [ "$CHAR_COUNT" -gt "$MAX_CHARS" ]; then
        EXCESS=$((CHAR_COUNT - MAX_CHARS))
        echo "❌ PROBLEMA: El archivo excede el límite por $EXCESS caracteres"
        echo "   Necesitas reducir $EXCESS caracteres antes de continuar"
        echo ""
        echo "💡 SUGERENCIAS PARA REDUCIR:"
        echo "   1. Eliminar secciones duplicadas"
        echo "   2. Simplificar descripciones"
        echo "   3. Consolidar reglas similares"
        echo "   4. Remover ejemplos redundantes"
        echo "   5. Acortar instrucciones verbosas"
        return 1
    else
        REMAINING=$((MAX_CHARS - CHAR_COUNT))
        echo "✅ El archivo está dentro del límite ($CHAR_COUNT/$MAX_CHARS caracteres)"
        echo "   Caracteres restantes: $REMAINING"
        return 0
    fi
}

# Ejecutar verificación
check_limit 