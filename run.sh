#!/usr/bin/env bash
cd src
env LD_LIBRARY_PATH=/usr/local/lib PYTHONUNBUFFERED=1 ./sdl_client.py
