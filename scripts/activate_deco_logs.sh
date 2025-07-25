#!/bin/bash

# Script para activar logs detallados para diagnosticar el problema de DECO
# Ayuda a identificar por qué el Custom GPT no usa DECO

echo "🔍 Activando logs detallados para diagnosticar DECO..."
echo "=================================================="

# Verificar logs actuales del servidor
echo "📊 Logs actuales del servidor:"
docker logs misuperapi --tail 20

echo ""
echo "🔍 Monitoreando llamadas HTTP en tiempo real..."
echo "Presiona Ctrl+C para detener el monitoreo"
echo ""

# Monitorear llamadas HTTP en tiempo real
docker logs misuperapi -f | grep -E "(get_question|deco/question|HTTP|Request)" &

# Guardar PID del proceso de monitoreo
MONITOR_PID=$!

echo "✅ Monitoreo activado. PID: $MONITOR_PID"
echo ""
echo "💡 INSTRUCCIONES:"
echo "1. Ahora conversa con el Custom GPT"
echo "2. Pide preguntas como 'dame una pregunta' o 'quiero estudiar filosofía'"
echo "3. Observa los logs para ver qué endpoint usa"
echo "4. Presiona Ctrl+C para detener el monitoreo"
echo ""

# Esperar a que el usuario presione Ctrl+C
trap "echo ''; echo '🛑 Monitoreo detenido'; kill $MONITOR_PID 2>/dev/null; exit 0" INT

# Mantener el script corriendo
while true; do
    sleep 1
done 