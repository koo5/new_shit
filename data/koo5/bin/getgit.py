#!/usr/bin/env python2
# -*- coding: utf-8 -*-


#this file is cc by-sa 3.0 with attribution required, because it is mostly just bits from SO pasted together

import json
import urllib2, urllib
import sys, os

try:
	import xdg.BaseDirectory
	cachedir = xdg.BaseDirectory.xdg_cache_home + '/getgit'
except:
	from os.path import expanduser
	cachedir = expanduser("~"+'/.getgit')



#http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
import os, errno
def mkdir_p(path):
	try:
		os.makedirs(path)
	except OSError as exc: # Python >2.5
		if exc.errno == errno.EEXIST and os.path.isdir(path):
			pass
		else: raise
#Update #For Python ≥ 3.2, os.makedirs has an optional third argument exist_ok that, when true, enables the mkdir -p functionality —unless mode is provided and the existing directory has different permissions than the intended ones; in that case, OSError is raised as previously.

mkdir_p(cachedir)

last_search = cachedir +'/'+"last_search"

def name_search(s):
	##TODO
	f = urllib2.urlopen("https://api.github.com/search/repositories?q=" + urllib.quote_plus(s)).read()
	#open("debug_result", "w").write(f)
	x = json.loads(f) #at least you didnt see my fuck ups except for that one
	r = []
	for i,j in enumerate(x['items']):
		 r.append((i, j['full_name'])) #todo: save the clone command here, along with the name
	return r

#all that needs to happen is for the top result to be selected automagically

def num_search(num):
	f = open(last_search, "r")
	g = json.load(f)
	for i in g:
		num = str(i[0])
		name = i[1]
		#print num, lookie, len(num), len(lookie), 
		if lookie == num:
			return name

"""two phase search, first enter text, get a list of numbered results, they are saved in last_results, then call this 
again with a number"""


if len(sys.argv) == 1:
	print "whatcha lookin for?"
else:
	lookie = sys.argv[1]

	if lookie.isdigit():
		name = num_search(lookie)
		if name == None:
			print "wat"
		else:
			cmd = "git clone https://github.com/"+name+".git"
			print name + " : " + cmd
			os.system(cmd)
	
	else:
		res = name_search(lookie)
		if not res:
			print "I can pretty safely say that there were no results."
		else:
			try:
				print "Cloning " + res[0][1] + "..."
				os.system("git clone https://github.com/"+res[0][1]+".git")
			except Exception as e:
				print "An error occured:", e

			print "other "+lookie+":"
			sans_first = res[1:]
			other = sans_first[:4]
			for i in other:
				print i[1]
			if len(other) < len(sans_first):
				print "..."

		#save it for later
		o = open(last_search, "w")
		json.dump(res, o, indent = 4)
		o.close()


