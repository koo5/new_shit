from lemon_args import args

import logging
logger=logging.getLogger("root")
info=logger.info
log=logger.debug

if not args.rpc:
	import server_frames as server
else:
	import pizco
	pizco.clientserver.set_excepthook()
	addy = open("addy", 'r').read()
	info("connecting to %s",addy)
	server = pizco.Proxy(addy)
	info('server is %s',server)
