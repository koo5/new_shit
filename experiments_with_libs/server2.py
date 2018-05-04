#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import Pyro4.naming

Pyro4.config.SERVERTYPE = "multiplex"
Pyro4.config.ONEWAY_THREADED = False
Pyro4.config.SERIALIZERS_ACCEPTED.add('msgpack')
Pyro4.config.SERIALIZERS_ACCEPTED.add('pickle')

import server_frames
objs = [("editor2", server_frames.editor)]

ns = Pyro4.naming.locateNS()

for name, obj in objs:
    name = "lemmacs.server_frames." + name
    
    use_unix_socket = False
    if use_unix_socket:
        import os
        if os.path.exists("example_unix.sock"):
             os.remove("example_unix.sock")
    try:
        existing = ns.lookup(name)
        if use_unix_socket:
            daemon = Pyro4.core.Daemon(unixsocket="example_unix.sock")
        else:
            daemon = Pyro4.core.Daemon(port=existing.port)
        daemon.register(obj, objectId=existing.object)
    except Pyro4.errors.NamingError:
        print("There was no previous registration in the name server.")
        if use_unix_socket:
            daemon = Pyro4.core.Daemon(unixsocket="example_unix.sock")
        else:
            daemon = Pyro4.core.Daemon()
        uri = daemon.register(obj)
        ns.register(name, uri)

print("Server started.")
daemon.requestLoop()

