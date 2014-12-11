
from lemon_args import args

if args.rpc:
	from lemon_utils.lemon_logging import log
	import pizco
	pizco.clientserver.set_excepthook()
	addy = open("addy", 'r').read()
	log("connecting to %s",addy)
	server = pizco.Proxy(addy)
	log('server is %s',server)
else:
	import server_frames as server


