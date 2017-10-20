#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sys import argv, stdout
from time import sleep, asctime
from subprocess import check_output


if len(argv) == 1:
	command = 'git diff --color=always;  grep "#crap"  -r src; head todo; grep "#todo"  -r src;'
else:
	command = argv[1]

while True:
	print (asctime())

	text = check_output(['sh', '-c', command]).decode()
	for line in text.split('\n'):
		sleep(1)
		print(line)
