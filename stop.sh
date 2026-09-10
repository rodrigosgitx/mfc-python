#!/bin/sh

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PID_FILE="$SCRIPT_DIR/server.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "No se encontró un emulador iniciado con start.sh."
    exit 1
fi

read -r SERVER_PID < "$PID_FILE"
kill -9 "$SERVER_PID"
rm "$PID_FILE"
echo "El emulador estaba corriendo con el PID $SERVER_PID. Ha sido matado"