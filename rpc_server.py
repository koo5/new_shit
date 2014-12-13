#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys, logging

from lemon_utils.lemon_logging import log

import pizco

import server_frames

pizco.LOGGER.addHandler(logging.StreamHandler(sys.stderr))
pizco.LOGGER.setLevel(logging.DEBUG)

s = pizco.Server(server_frames)
addy = s.rep_endpoint
open("addy", "w").write(str(addy))
log('serving %s on %s', server_frames, addy)
s.serve_forever()


"""
pizco missing features:
 _multiobject branch. the de-ooped structure of server_Frames is a no-brainer to revert, but this form could become a hassle.
 remote generators (streams in zerorpc)
 msgpack instead of json? pickle should be fine
"""
