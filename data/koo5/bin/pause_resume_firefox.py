#!/usr/bin/env python3
import sys
import subprocess
program = 'firefox'
if len(sys.argv) == 2:
	program = sys.argv[1]
x =  subprocess.check_output("ps -l -A | grep " + program, shell = True).decode()
print(x)
y = x.splitlines()
sig = 'CONT'
for l in y:
	if l[2] != 'T':
		sig = "STOP"
print(subprocess.check_output("killall -s " + sig + " " + program, shell = True))

