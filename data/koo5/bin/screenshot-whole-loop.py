#!/usr/bin/env python2.7
import os, time
while True:
	time.sleep(2)
	os.system("scrot  -q 80 /home/kook/screenshots/$(date +%Y%m%d%H%M%S).png")
