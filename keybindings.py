#maybe when we have multiple editor frames instead of one "root" frame,
#we will want to just pass the event on to perhaps the previously focused frame
#for now im trying having all top level handlers in one file here

#todo:look into FRP

def keypress(e):
	k = e.key

#with CTRL

	ctrl = KMOD_CTRL & event.mod

	if k == K_F1:
		cycle_sidebar()
	elif ctrl and event.uni == '=':
		change_font_size(1)
	elif ctrl and event.uni == '-':
		change_font_size(-1)


	if KMOD_CTRL & e.mod:
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
			server.bye()

#with CTRL on SDL

		elif platform.frontend == platform.sdl:
			if e.key == K_UP:
				sidebar.move(-1)
			elif e.key == K_DOWN:
				sidebar.move(1)
			else:
				return False

# with CTRL on CURSES

		elif platform.frontend == platform.curses:
			if e.key == K_INSERT: # todo: find better keybindings for curses
				sidebar.move(-1)
			elif e.key == K_DELETE:
				sidebar.move(1)
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
			return menu.accept()
		else:
			return False
