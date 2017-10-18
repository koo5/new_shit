#!/usr/bin/env python2.7
import os, time
for i in range(1,33):
	cmd = "xset  -led " + str(i)
	print cmd
	os.system(cmd)
	
