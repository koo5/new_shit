#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import Pyro4.naming


Pyro4.config.ONEWAY_THREADED = False
Pyro4.config.SERIALIZERS_ACCEPTED.add('msgpack')
Pyro4.config.SERIALIZERS_ACCEPTED.add('pickle')


print("Autoreconnect using Pyro Name Server.")


import server_frames

objs = [("editor", server_frames.editor)]



# If we reconnect the object, it has to have the same objectId as before.
# for this example, we rely on the Name Server registration to get our old id back.
# If we KNOW 100% that PYRONAME-uris are the only thing used to access our
# object, we could skip all this and just register as usual.
# That works because the proxy, when reconnecting, will do a new nameserver lookup
# and receive the new object uri back. This REQUIRES:
#   - clients will never connect using a PYRO-uri
#   - client proxy._pyroBind() is never called
# BUT for sake of example, and because we really cannot guarantee the above,
# here we go for the safe route and reuse our previous object id.

ns = Pyro4.naming.locateNS()

for name, obj in objs:
    name = "lemmacs." + name
    try:
        existing = ns.lookup(name)
        print("Object still exists in Name Server with id: %s" % existing.object)
        print("Previous daemon socket port: %d" % existing.port)
        # start the daemon on the previous port
        daemon = Pyro4.core.Daemon(port=existing.port)

        # register the object in the daemon with the old objectId
        daemon.register(obj, objectId=existing.object)

    except Pyro4.errors.NamingError:
        print("There was no previous registration in the name server.")
        # just start a new daemon on a random port
        daemon = Pyro4.core.Daemon()
        # register the object in the daemon and let it get a new objectId
        # also need to register in name server because it's not there yet.

        uri = daemon.register(obj)
        ns.register(name, uri)

print("Server started.")
daemon.requestLoop()

# note: we are not removing the name server registration when terminating!
