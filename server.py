
from lemon_utils.lemon_args import args

if args.rpc:
	import pizco
	server = pizco.Proxy(open("addy", 'r').read())
	server.connect()
else:
	import server_frames as server


