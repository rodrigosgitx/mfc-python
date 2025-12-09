#!/bin/sh

# Build logs symbolic lync
if [ ! -d logs ]; then
    mkdir logs
fi

python3 loopBase.py > /dev/null &
sleep 2

# Generate a file with the pid
SERVER_PID=$!

echo $SERVER_PID > server.pid

echo "Emulador corriendo con PID:" $SERVER_PID
