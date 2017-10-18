#!/usr/bin/env python2.7
import os, time, sys
while True:
	os.system("sudo " + os.path.dirname(os.path.abspath(__file__)) + "/" + "snap.fish")
	time.sleep(int(sys.argv[1]))
