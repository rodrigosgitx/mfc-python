#!/usr/bin/env sh

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python3 -m pip install --target "$SCRIPT_DIR" -r "$SCRIPT_DIR/dependencies.txt"