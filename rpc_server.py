import pizco

import server

s = pizco.Server(server) #, "tcp://127.0.0.1:13000")
open("addy", "w").write(str(s.rep_endpoint))
s.serve_forever()

