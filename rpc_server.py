import pizco

import server_frames


s = pizco.Server(server_frames)
open("addy", "w").write(str(s.rep_endpoint))
s.serve_forever()


"""
pizco missing features:
 _multiobject branch. the de-ooped structure of server_Frames is a no-brainer to revert, but this form could become a hassle.
 remote generators (streams in zerorpc)
 msgpack instead of json? pickle should be fine
"""
