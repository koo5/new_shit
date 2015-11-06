from types import SimpleNamespace

from lemon_utils.lemon_six import iteritems, unicode
from lemon_utils.dotdict import Dotdict
from lemon_utils.lemon_logging import info,log
from lemon_args import args


try:
	#im gonna have to ditch this crappy module
	from colors import *
	assert rgb,  'we imported some outdated .pyc or something'
except ImportError as e:
	info("%s, ...but nevermind", e)


class ColorsSettings():
	def __init__(s):
		s.info_item_text = (224,224,224)
		s.bg = (0,0,0)
		s.highlighted_bg = (40,0,0)
		s.arrow = (250,250,111)
		s.arrow_fail = (150,150,211)
		s.fg = (255,255,255)
		s.cursor = (155,255,255)
		s.info_item_visibility_toggle = (100,100,100)
		s.menu_rect_selected = (255,255,255)
		s.menu_rect = (0,0,255)
		s.help = (255,255,0)
		s.parser_hint = (100,100,100)
		s.text_brackets = (0,255,0)
		s.compiler_brackets = (255,255,0)
		s.node_brackets = (250,150,150)
		s.number_buttons = (80,80,255)
		s.menu_item_extra_info = (0,200,0)
		s.eval_results = (150,150,150)
		s.parser_menu_item_brackets = (0,255,255)
		s.default_parser_menu_item_brackets  = (0,0,255)
		s.element_brackets = (200,200,200)
		s.widget_color = (150,150,255)
		s.button = (255,150,150)

def cache():
	global invert, mono
	invert = args.invert
	mono = args.mono
	for k,v in iteritems(default_colors.__dict__):
		colors.__dict__[k] = modify(v)

def modify(c, max=255):
	if mono and c != (0,0,0):
		c = (255,255,255)
	if invert:
		c = (max - c[0], max - c[1], max - c[2])
	assert(isinstance(c, tuple))
	return c

default_colors = ColorsSettings()
colors = ColorsSettings()
cache()