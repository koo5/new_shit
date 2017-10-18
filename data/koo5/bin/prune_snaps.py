#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import dateutil.parser
import datetime
import sys, os
from dotdict import Dotdict


def prune_snaps(path):
	ss = os.listdir(path)
	print(path + ":")
	snaps = []
	for s in ss:
		p = path + "/" + s
		print(p)
		snaps.append(	Dotdict({'path':p,
		'time':dateutil.parser.parse(s)}))
	
	def prune(snaps, l1, l2):
		h = None

		for i in snaps:
			t = i.time
			#import IPython; IPython.embed()
			if t.__getattribute__(l1) == datetime.datetime.utcnow().__getattribute__(l1):
				break
			if h == t.__getattribute__(l2):
				os.system("btrfs subvolume delete " + i.path)
			h = t.__getattribute__(l2)
	


	prune(snaps, "day", "hour")
	prune(snaps, "month", "day")

if __name__ == '__main__':
	prune_snaps(sys.argv[1])
