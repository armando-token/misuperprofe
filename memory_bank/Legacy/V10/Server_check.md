# 🛠️ Plan de Revisión Integral del Servidor Misuperprofe Tutor IA
1. Verificación de Contenedores y Recursos del Sistema
[ ] Listar todos los contenedores Docker y verificar que estén en estado "Up" y "healthy".
Comando: docker ps -a
[ ] Verificar uso de disco.
Comando: df -h
[ ] Verificar uso de memoria RAM.
Comando: free -h
[ ] Verificar carga promedio del sistema.
Comando: uptime
2. Servicios Principales
[ ] Backend (web/FastAPI) activo y saludable.
[ ] Base de datos PostgreSQL activa y saludable.
[ ] Redis activo y saludable.
3. Monitorización y Métricas
[ ] Prometheus activo y saludable.
Comando: curl -s http://localhost:9090/-/healthy
[ ] Grafana activo y saludable.
Comando: curl -s http://localhost:3000/api/health
[ ] Loki, Promtail, Node Exporter, Postgres Exporter, Nginx Exporter activos.
Comando: docker ps -a (verificar nombres y estado)
4. Pruebas de Endpoints Críticos
[ ] /health — Estado del backend.
Comando: curl -s http://localhost:8000/health
[ ] /ask — Consulta teórica.
Comando: curl -s -X POST http://localhost:8000/ask -H 'Content-Type: application/json' -H 'Authorization: Bearer <API_KEY>' -d '{"pregunta": "¿Qué es la biología?"}'
[ ] /get_question — Práctica individual.
Comando: curl -s -X GET 'http://localhost:8000/get_question?course=biologia' -H 'Authorization: Bearer <API_KEY>'
[ ] /api/courses — Listado de cursos.
Comando: curl -s -X GET 'http://localhost:8000/api/courses' -H 'Authorization: Bearer <API_KEY>'
[ ] /api/lesson/leaderboard — Ranking semanal.
Comando: curl -s -X GET 'http://localhost:8000/api/lesson/leaderboard?requesting_user_id=programas@misuperprofe.com&league_id=global_weekly&top_n=10' -H 'Authorization: Bearer <API_KEY>'
[ ] /user_stats — Estadísticas de usuario.
Comando: curl -s -X GET 'http://localhost:8000/user_stats?user_id=programas@misuperprofe.com' -H 'Authorization: Bearer <API_KEY>'
[ ] /api/lesson/start y /api/lesson/answer — Lecciones adaptativas.
Comando: Verificar inicio y respuesta de lección.
5. Pruebas de Scripts de Mantenimiento
[ ] Ejecutar scripts de limpieza y mantenimiento (por ejemplo, spaced repetition).
Comando: export POSTGRES_HOST=localhost && python3 scripts/clean_spaced_repetition.py
[ ] Ejecutar scripts de carga de teoría si es necesario.
6. Verificación de Logs y Errores
[ ] Revisar logs recientes de la aplicación y servicios.
Comando: tail -n 40 nohup.out
Comando: docker logs <nombre_contenedor> --tail 40
7. Verificación de Backups y Documentación
[ ] Verificar existencia y fecha de backups recientes.
[ ] Confirmar que la documentación (progress.md, CustomGPT.md) está actualizada.
8. Checklist de Servicios Auxiliares
[ ] Todos los servicios definidos en docker-compose.yml están activos.
Comando: docker-compose ps
[ ] Si algún servicio no está activo, levantarlo con:
Comando: docker-compose up -d <servicio>
9. Notas y Recomendaciones
Documentar cualquier error, bug o anomalía detectada.
Registrar todos los pasos y resultados en progress.md para trazabilidad.
Si se detecta un bug (por ejemplo, enums en lecciones adaptativas), documentar el error y el contexto.