#!/usr/bin/env bash
# tools/export_code_for_o3.sh
#
# Genera ntid_code_only.zip con TODO el código fuente
# y levanta un servidor HTTP temporal para descargarlo.

set -e            # abortar si algo falla
PORT=8001         # puedes cambiarlo
ZIP=ntid_code_only.zip

echo "🔄  Limpiando ZIP anterior…"
rm -f "$ZIP"

echo "📦  Empaquetando código fuente…"
## 1️⃣ Lista blanca de carpetas / archivos
zip -r "$ZIP" \
  ntid/                        \
  app/                         \
  content/                     \
  tasks/                       \
  tools/                       \
  tests/                       \
  memory_bank/                 \
  static/                      \
  Dockerfile docker-compose.yml pyproject.toml requirements*.txt \
  README.md .env.example \
  -x '*.pyc' '*.log' '__pycache__/*' '.git/*' '.gitignore' \
  -x 'backup_*/*' 'backup_files/*' '.cache/*' 'loki/*' 'prometheus/*'

echo "✅  ZIP generado: $(du -h $ZIP | cut -f1)"

## 2️⃣ Servidor HTTP temporal
echo "🚀  Iniciando servidor HTTP en http://$HOSTNAME:$PORT/"
echo "    ➜  URL directa ZIP: http://$(curl -s ifconfig.me):$PORT/$ZIP"
echo "    (Ctrl-C para detener)"

python3 -m http.server "$PORT"
# Añade al bloque -x
-x '*.db' '*.sqlite' \
-x 'venv/*' '.venv/*' \
-x '**/__pycache__/*' \
-x 'backup_*/*' 'grafana/*' 'loki/*' 'prometheus/*' \
-x '*.log' 'tests/large_fixtures/*'

