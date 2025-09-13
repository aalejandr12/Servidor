#!/bin/bash
cd /opt/pdfapi

# Intentar detener el proceso existente
pkill -f "uvicorn main:app" 2>/dev/null || true

# Esperar un momento
sleep 3

# Activar el entorno virtual e iniciar el servidor
source .venv/bin/activate
nohup .venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 3001 --workers 1 --reload > server.log 2>&1 &

echo "Servidor reiniciado en puerto 3001. PID: $!"
echo "Logs en server.log"