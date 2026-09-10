#!/bin/sh

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR/main" || exit 1

if [ ! -d logs ]; then
    mkdir logs
fi

python3 loopBase.py > /dev/null &
SERVER_PID=$!

echo "$SERVER_PID" > "$SCRIPT_DIR/server.pid"
echo "Emulador corriendo con PID: $SERVER_PID"