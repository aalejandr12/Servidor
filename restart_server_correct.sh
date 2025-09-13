#!/bin/bash
cd /opt/pdfapi

# Detener el proceso en puerto 3000
kill $(ps aux | grep 'uvicorn main:app.*port 3000' | grep -v grep | awk '{print $2}') 2>/dev/null || true

# Esperar un momento para que el puerto se libere
sleep 3

# Iniciar el servidor en el puerto correcto con auto-reload
source .venv/bin/activate
nohup .venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 3000 --reload > server.log 2>&1 &

echo "Servidor reiniciado en puerto 3000 (puerto del proxy). PID: $!"
echo "Logs en server.log"