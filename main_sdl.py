#!/usr/bin/python
# -*- coding: utf-8 -*-


os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '1'
import pygame
from pygame import display, image

import lemon
from lemon import logframe, root, sidebar
from lemon import args

def change_font_size(by = 0):
	args.font_size += by
	frames.font = pygame.font.SysFont('monospace', args.font_size)
	frames.font_width, frames.font_height = frames.font.size("X")

def resize(size):
	global screen_surface, screen_width, screen_height
	log("resize to "+str(size))
	screen_surface = pygame.display.set_mode(size, flags)
	screen_width, screen_height = screen_surface.get_size()
	resize_frames()

def resize_frames():
	lemon.logframe.rect.height = log_height = 110
	lemon.logframe.rect.width = screen_width
	lemon.logframe.rect.topleft = (0, screen_height - log_height)

	lemon.root.rect.topleft = (0,0)
	lemon.root.rect.width = screen_width / 3 * 2
	lemon.root.rect.height = screen_height - log_height

	sidebar_rect = Rect()
	sidebar_rect.topleft = (root.rect.w, 0)
	sidebar_rect.width = screen_width - lemon. root.rect.width
	sidebar_rect.height = root.rect.height
	for frame in lemon.sidebars:
		frame.rect = sidebar_rect

def top_keypress(event):
	ctrl = pygame.KMOD_CTRL & event.mod
	#first platform specific stuff
	if ctrl and event.uni == '=':
		change_font_size(1)
	elif ctrl and event.uni == '-':
		change_font_size(-1)
	else:
	#then general
		return lemon.top_keypress()
	return True


def keypress(e):
	reset_cursor_blink_timer()
	if args.log_events:
		log(e)
	lemon.keypress()
	render()
	draw()
	"""
	try:
		gc.collect()
		objgraph.show_most_common_types(30)
	except:
		pass
	"""


def mousedown(e):
	reset_cursor_blink_timer()
	#handle ctrl + mousewheel font changing
	if e.button in [4,5] and (
		pygame.key.get_pressed()[pygame.K_LCTRL] or
		pygame.key.get_pressed()[pygame.K_RCTRL]):
		if e.button == 4: change_font_size(1)
		if e.button == 5: change_font_size(-1)
		render()
		draw()
	else:
		lemon.mousedown(lemon.MousedownEvent(e.pos, e.button))
		draw()


def process_event(event):

	if event.type == pygame.USEREVENT:
		pass # we woke up python to poll for SIGINT

	if event.type == pygame.USEREVENT + 1:
		root.cursor_blink_phase = not root.cursor_blink_phase
		draw()

	if event.type == pygame.QUIT:
		bye()

	lemon.input_pygame_event(event)

	if event.type == pygame.VIDEORESIZE:
		resize(event.size)
		render()

	if event.type == pygame.ACTIVEEVENT:
		if event.gain:
			reset_cursor_blink_timer()
		else:
			pygame.time.set_timer(pygame.USEREVENT + 1, 0)#disable
			root.cursor_blink_phase = False
		draw()



def reset_cursor_blink_timer():
	if not args.dontblink:
		pygame.time.set_timer(pygame.USEREVENT + 1, 800)
	root.cursor_blink_phase = True



def render():
	root.render()
	sidebar.render()
	logframe.render()


def draw():
	if not lemon.fast_forward:
		screen_surface.blit(root_draw(lemon.root, new_surface()), root.rect.topleft)
		screen_surface.blit(sidebar_draw(lemon.sidebar), sidebar.rect.topleft)
		screen_surface.blit(logframe_draw(lemon.logframe), logframe.rect.topleft)
		pygame.display.flip()



from pygame import draw

def new_surface(self):
	surface = pygame.Surface((self.rect.w, self.rect.h), 0)
	if colors.bg != (0,0,0):
		surface.fill(colors.bg)

def draw_lines(self, surf, highlight=None, transparent=False, justbg=False):
	bg_cached = color("bg")
	for row, line in enumerate(self.lines):
		for col, char in enumerate(line):
			x = font_width * col
			y = font_height * row
			bg = color("highlighted bg" if (
				'node' in char[1] and
				char[1]['node'] == highlight and
				not args.eightbit) else "bg")
			if justbg:
				if bg != bg_cached:
					pygame.draw.rect(surf,bg,(x,y,font_width,font_height))
			#	sur = font.render(' ',0,(0,0,0),bg)#guess i could just make a rectangle
			else:
				fg = color(char[1]['color'])
				if transparent:
					sur = font.render(char[0],1,fg)
				else:#its either arrows or highlighting, you cant have everything, hehe
					sur = font.render(char[0],1,fg,bg)
				surf.blit(sur,(x,y))







def bye():
	log("deading")
	pygame.display.iconify()
	sys.exit()

def loop():
	process_event(pygame.event.wait())




pygame.display.init()
pygame.font.init()
flags = pygame.RESIZABLE|pygame.DOUBLEBUF
display.set_caption('lemon operating language v' + lemon.version)
icon = image.load('icon32x32.png')
display.set_icon(icon)
change_font_size()



def fuck_sdl():
	"""SDL insists that you must give your new window some size
	(screen_surface = pygame.display.set_mode), it ignores the WM
	but if the WM takes over...it doesnt even realize it!
	so it thinks it has the original size
	so i try to get the actual window size and "resize" """
	w = pygame.display.get_wm_info()["wmwindow"]
	import subprocess
	x =  subprocess.check_output(["xwininfo", "-id", str(w)])
	y = x.splitlines()
	for l in y:
		s = l.split()
		if len(s) > 1:
			if s[0] == "Width:":
				w = int(s[1])
			if s[0] == "Height:":
				h = int(s[1])
	return w,h

resize((666,666))
try:
	resize(fuck_sdl())
except Exception as e:
	print e, "failed to work around stupid sdl, will continue thinking the window is 666x666, please do a manual resize"


#try to set SDL keyboard settings to system settings
try:
	s = os.popen('xset -q  | grep "repeat delay"').read().split()
	repeat_delay, repeat_rate = int(s[3]), int(s[6])
	pygame.key.set_repeat(repeat_delay, 1000/repeat_rate)
except Exception as e:
	print e, "cant fix sdl keyboard repeat delay/rate"




pygame.time.set_timer(pygame.USEREVENT, 777) #poll for SIGINT
reset_cursor_blink_timer()
def main():
	while True:
		try:
			loop()
	#	except KeyboardInterrupt() as e:
	#		pygame.display.iconify()
	#		raise e
		except:
			pygame.display.iconify()
			raise

if __name__ == "__main__":
	main()
