import sys

if hasattr(sys, 'pypy_version_info'):
	print ("trying to load pygame_cffi, adding pygame_cffi to sys.path")
	try:
		sys.path.append("pygame_cffi")
		import pygame
	except e:
		print(e)
		sys.path.remove("pygame_cffi")
import pygame
if hasattr(pygame, 'cffi'):
		print("loaded pygame_cffi")
