import pizco

import server

"""
class MyServer(pizco.Server):
	def return_as_remote(s, attr):
		return True # return all the server module globals as remotes
"""

first_server = dict(
	intro =

s = MyServer(first_server) #, "tcp://127.0.0.1:13000")
open("addy", "w").write(str(s.rep_endpoint))
s.serve_forever()

