import pizco
server = pizco.Proxy(open("addy", 'r').read())

def bla(x):
	print "BLA"+x

server.log_on_add.connect(bla)



server.log_add("hello")
import time
time.sleep(2)
