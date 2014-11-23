
def keypress(event):

	k = event.key

#with CTRL

	if KMOD_CTRL & event.mod:
		if k == K_LEFT:
			root.prev_elem()
		elif k == K_RIGHT:
			root.next_elem()
		elif k == K_HOME:
			root.cursor_top()
		elif k == K_END:
			root.cursor_bottom()
		elif k == K_f:
			root.dump_to_file()
		elif k == K_q:
			import sys
			syroot.exit()#a quit shortcut that goes thru the event pickle/replay mechanism

#with CTRL on SDL

		elif platform.frontend == platform.sdl:
			if e.key == K_UP:
				self.move(-1)
			elif e.key == K_DOWN:
				self.move(1)
			elif e.key == K_m:
				self.menu_dump()
			else:
				return False

# with CTRL on CURSES

		elif platform.frontend == platform.curses:
			if e.key == K_INSERT:
				self.move(-1)
			elif e.key == K_DELETE:
				self.move(1)
			else:
				return False

# with no modifier keys

	else:
		if k == K_F8:
			root.toggle_arrows()
		elif k == K_UP:
			root.move_cursor_v(-1)
			root.and_sides(event)
		elif k == K_DOWN:
			root.move_cursor_v(+1)
			root.and_sides(event)
		elif k == K_LEFT:
			root.move_cursor_h(-1)
			root.and_updown(event)
		elif k == K_RIGHT:
			root.move_cursor_h(+1)
			root.and_updown(event)
		elif k == K_HOME:
			root.cursor_home()
		elif k == K_END:
			root.cursor_end()
		elif k == K_PAGEUP:
			root.move_cursor_v(-10)
		elif k == K_PAGEDOWN:
			root.move_cursor_v(10)
		if e.uni == ' ':
			return self.accept()
		else:
			return False
h
