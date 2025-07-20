#!/bin/bash
# Healthcheck de servicios críticos para el backend educativo
# Uso: bash scripts/healthcheck.sh

SERVICIOS=(web db redis)
FALTANTES=()

# Comprobar estado de cada servicio
for SVC in "${SERVICIOS[@]}"; do
    STATUS=$(docker-compose ps --services --filter "status=running" | grep "^$SVC$")
    if [[ -z "$STATUS" ]]; then
        FALTANTES+=("$SVC")
    fi
done

if [[ ${#FALTANTES[@]} -eq 0 ]]; then
    echo "✅ Todos los servicios críticos están levantados: ${SERVICIOS[*]}"
    exit 0
else
    echo "❌ Los siguientes servicios NO están levantados: ${FALTANTES[*]}"
    echo "Puedes levantarlos con: docker-compose up -d ${FALTANTES[*]}"
    exit 1
fi 