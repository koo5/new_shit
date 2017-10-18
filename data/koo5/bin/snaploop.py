#!/usr/bin/env python2.7
import os, time, sys
while True:
	os.system("sudo " + os.path.dirname(os.path.abspath(__file__)) + "/" + "prune_snaps.py " + sys.argv[3])
	os.system("sudo " + os.path.dirname(os.path.abspath(__file__)) + "/" + "snap.fish " + sys.argv[2] + " " + sys.argv[3])
	time.sleep(int(sys.argv[1]))
