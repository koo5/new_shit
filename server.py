
from lemon_args import args

if args.rpc:
	import pizco
	server = pizco.Proxy(open("addy", 'r').read())
else:
	import server_frames as server


