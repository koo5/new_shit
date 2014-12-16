from lemon_utils.lemon_logging import log
from lemon_args import args

if not args.rpc:
	import server_frames as server
else:
	import pizco
	pizco.clientserver.set_excepthook()
	addy = open("addy", 'r').read()
	log("connecting to %s",addy)
	server = pizco.Proxy(addy)
	log('server is %s',server)
