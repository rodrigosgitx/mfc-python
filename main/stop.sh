#!/bin/sh

read SERVER_PID < server.pid
kill -9 $SERVER_PID
rm server.pid
echo "El emulador estaba corriendo con el PID " $SERVER_PID ". Ha sido matado"
