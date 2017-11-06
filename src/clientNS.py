#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import Pyro4

#Pyro4.config.SERIALIZER = "marshal"
#Pyro4.config.SERIALIZER = "msgpack"

print("Autoreconnect using Name Server.")
obj = Pyro4.core.Proxy("PYRONAME:lemmacs.editor")

obj._pyroSerializer = "msgpack"
obj._pyroSerializer = "pickle"
#obj._pyroSerializer = "marshal"

#from IPython import embed; embed()

def collect_tags(obj):
	print("collect_tags(%s)"%obj)
	t = (obj.collect_tags())
	#print(t)
	for i in t:
		for j in i:
			#continue
			if type(j) == str:
				sys.stdout.write(j)



def loop():
    print("call...")
    try:
        collect_tags(obj)
        print("Sleeping 1 second")
        time.sleep(1)
    except Pyro4.errors.ConnectionClosedError:  # or possibly CommunicationError
        print("Connection lost. REBINDING...")
        print("(restart the server now)")
        obj._pyroReconnect()



if __name__ == "__main__":
    while True:
        loop()
