#!/bin/bash
pico2wave -l=en-US -w=/tmp/test.wav "$1"
aplay /tmp/test.wav
