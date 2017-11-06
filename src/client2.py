#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import logging
import sys
import Pyro4


Pyro4.config.ONEWAY_THREADED = False
Pyro4.config.SERIALIZERS_ACCEPTED.add('msgpack')
Pyro4.config.SERIALIZERS_ACCEPTED.add('pickle')



# initialize the logger so you can see what is happening with the callback exception message:
logging.basicConfig(stream=sys.stderr, format="[%(asctime)s,%(name)s,%(levelname)s] %(message)s")
log = logging.getLogger("Pyro4")
log.setLevel(logging.WARNING)


class CallbackHandler(object):
	@Pyro4.oneway
	@Pyro4.expose
#	@Pyro4.callback
	def callback(self, tags):
		#print(tags)
		for j in tags:
			
			if type(j) == str:
				continue
				sys.stdout.write(j)
			elif j == -1:
				print ("done")
				#from IPython import embed; embed()
				daemon.shutdown()



obj = Pyro4.core.Proxy("PYRONAME:lemmacs.server_frames2.editor")
#obj._pyroSerializer = "msgpack"
#obj._pyroSerializer = "pickle"


daemon=0
def collect():
	global daemon
	daemon = Pyro4.core.Daemon()
	callback_handler = CallbackHandler()
	daemon.register(callback_handler)

	print("start_collecting_tags(%s)"%obj)
	obj.start_collecting_tags(callback_handler)

	print("waiting for callbacks to arrive...")
	print("(ctrl-c/break the program once it's done)")

	daemon.requestLoop()


if __name__ == "__main__":
	for i in range(5):	
		collect()
