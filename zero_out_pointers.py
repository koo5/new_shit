#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, re
for l in sys.stdin.readlines():
	l = re.sub(r"0x[0-9a-f]+", '0xXXXXXXXXXXXX', l)
	sys.stdout.write(l)
