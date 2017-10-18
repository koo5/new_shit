--- dotdict.py	(original)
+++ dotdict.py	(refactored)
@@ -12,7 +12,7 @@
 			object.__setattr__(s, "_dict", dict())#weird, shouldnt it set the value, not an empty dict?
 		else:
 			if object.__getattribute__(s, "_locked"):
-				if not k in s._dict.iterkeys():
+				if not k in iter(s._dict.keys()):
 					raise Exception("setting an unknown item of a locked-down Dotdict")
 			s._dict[k] = v
 	def __getattr__ (s, k):
--- element.py	(original)
+++ element.py	(refactored)
@@ -65,7 +65,7 @@
 		for c in mro:
 			#log(cls)
 			#iterate thru all methods and other stuff declared in that class:
-			for member_name, member in c.__dict__.iteritems():
+			for member_name, member in c.__dict__.items():
 				#if member_name == "delete_self":
 				#	log ("!!!" + str(member))
 				#the levent decorator was here:
@@ -74,12 +74,12 @@
 					#dicts aren't hashable, so lets convert the constraints dict
 					# to a tuple and save the dict in the value
 					#by "constraints" is meant the key combinations
-					hash = tuple(member.levent_constraints.iteritems())
+					hash = tuple(member.levent_constraints.items())
 					r[hash] = (member.levent_constraints, member_name, member)
 				else:
 					#look if a previously found event handler function
 					# is overriden in child class, this time not wrapped
-					for hash,(constraints,name,function) in r.iteritems():
+					for hash,(constraints,name,function) in r.items():
 						if name == member_name:
 							#log("updating override")
 							#its overriden in a child class
@@ -90,7 +90,7 @@
 
 	def dispatch_levent(s, e):
 		#log('dispatching '+str(e))
-		for constraints, function_name, function in s.levent_handlers.itervalues():
+		for constraints, function_name, function in s.levent_handlers.values():
 			#log ("for constraint" + str(constraints))
 			if "key" in constraints:
 				if constraints['key'] != e.key:
--- event.py	(original)
+++ event.py	(refactored)
@@ -208,7 +208,7 @@
                 for name in dir(object):
                     if name in self.event_types:
                         yield name, getattr(object, name)
-        for name, handler in kwargs.items():
+        for name, handler in list(kwargs.items()):
             # Function for handling given event (no magic)
             if name not in self.event_types:
                 raise EventException('Unknown event "%s"' % name)
@@ -391,7 +391,7 @@
         n_handler_args = len(handler_args)
 
         # Remove "self" arg from handler if it's a bound method
-        if inspect.ismethod(handler) and handler.im_self:
+        if inspect.ismethod(handler) and handler.__self__:
             n_handler_args -= 1
 
         # Allow *args varargs to overspecify arguments
@@ -407,9 +407,9 @@
         if n_handler_args != n_args:
             if inspect.isfunction(handler) or inspect.ismethod(handler):
                 descr = '%s at %s:%d' % (
-                    handler.func_name,
-                    handler.func_code.co_filename,
-                    handler.func_code.co_firstlineno)
+                    handler.__name__,
+                    handler.__code__.co_filename,
+                    handler.__code__.co_firstlineno)
             else:
                 descr = repr(handler)
             
@@ -449,7 +449,7 @@
             name = func.__name__
             self.set_handler(name, func)
             return args[0]
-        elif type(args[0]) in (str, unicode):   # @window.event('on_resize')
+        elif type(args[0]) in (str, str):   # @window.event('on_resize')
             name = args[0]
             def decorator(func):
                 self.set_handler(name, func)
--- frames.py	(original)
+++ frames.py	(refactored)
@@ -34,7 +34,8 @@
 		s.lines = project.project(s,
 		    s.cols, s, s.scroll_lines + s.rows).lines[s.scroll_lines:]
 
-	def under_cr(self, (c, r)):
+	def under_cr(self, xxx_todo_changeme):
+		(c, r) = xxx_todo_changeme
 		try:
 			return self.lines[r][c][1]["node"]
 		except:
@@ -70,7 +71,8 @@
 		return self.rect.w / font_width
 
 
-def xy2cr((x, y)):
+def xy2cr(xxx_todo_changeme1):
+	(x, y) = xxx_todo_changeme1
 	c = x / font_width
 	r = y / font_height
 	return c, r
@@ -101,7 +103,7 @@
 	def first_nonblank(self):
 		r = 0
 		for ch, a in self.lines[self.cursor_r]:
-			if ch in [" ", u" "]:
+			if ch in [" ", " "]:
 				r += 1
 			else:
 				return r
@@ -157,11 +159,11 @@
 				assert(isinstance(l, list))
 				for i in l:
 					assert(isinstance(i, tuple))
-					assert(isinstance(i[0], str) or isinstance(i[0], unicode))
+					assert(isinstance(i[0], str) or isinstance(i[0], str))
 					assert(len(i[0]) == 1)
 					assert(isinstance(i[1], dict))
 					assert(i[1]['node'])
-					assert(i[1].has_key('char_index'))
+					assert('char_index' in i[1])
 
 	#todo: clean this up ugh, oh and arrows are broken, the source point stays stuck when you scoll
 	def complete_arrows(self, arrows):
@@ -428,7 +430,7 @@
 
 
 	def click(s,e,pos):
-		for i,r in s.rects.iteritems():
+		for i,r in s.rects.items():
 			if collidepoint(r, pos):
 				s.sel = s.items_on_screen.index(i)
 				s.accept()
@@ -452,7 +454,7 @@
 
 def collidepoint(r, pos):
 	x, y = pos
-	print x,y,r
+	print(x,y,r)
 	return x >= r[0] and y >= r[1] and x < r[0] + r[2] and y < r[1] + r[3]
 
 
--- lemon_colors.py	(original)
+++ lemon_colors.py	(refactored)
@@ -34,7 +34,7 @@
 	global colors, invert, mono
 	invert = args.invert
 	mono = args.mono
-	colors._dict.update(dict([(k, modify(v)) for k,v in default_colors.iteritems()]))
+	colors._dict.update(dict([(k, modify(v)) for k,v in default_colors.items()]))
 
 def modify(c, max=255):
 	if mono and c != (0,0,0):#||(0,0,0,0)
--- lemon.py	(original)
+++ lemon.py	(refactored)
@@ -70,7 +70,7 @@
 
 class KeypressEvent(object):
 	def __init__(self, e, all):
-		self.uni = e.unicode
+		self.uni = e.str
 		self.key = e.key
 		self.mod = e.mod
 		self.all = all
@@ -189,7 +189,7 @@
 		try:
 			pickle.dump(e, f)
 		except pickle.PicklingError as error:
-			print error, ", are you profiling?"
+			print(error, ", are you profiling?")
 
 def render():
 	root.render()
@@ -202,7 +202,7 @@
 		root.cursor_c, root.cursor_r = project.find(root.root['program'].ch.statements.items[0], root.lines)
 		root.cursor_c += 1
 	except Exception as e:
-		print e, ", cant set initial cursor position"
+		print(e, ", cant set initial cursor position")
 	if args.replay:
 		do_replay(True)
 	render()
--- main_sdl.py	(original)
+++ main_sdl.py	(refactored)
@@ -209,7 +209,7 @@
 	draw_rects(s, surface)
 
 def draw_rects(s, surface):
-	for i,r in s.rects.iteritems():
+	for i,r in s.rects.items():
 		if i == s.selected:
 			c = colors.menu_rect_selected
 		else:
@@ -262,14 +262,14 @@
 	try:
 		resize(fuck_sdl())
 	except Exception as e:
-		print e, "failed to work around stupid sdl, will continue thinking the window is 666x666, please do a manual resize"
+		print(e, "failed to work around stupid sdl, will continue thinking the window is 666x666, please do a manual resize")
 
 	repeat_delay, repeat_rate = 300, 30
 	try:#try to set SDL keyboard settings to system settings
 		s = os.popen('xset -q  | grep "repeat delay"').read().split()
 		repeat_delay, repeat_rate = int(s[3]), int(s[6])
 	except Exception as e:
-		print "cant get system keyboard repeat delay/rate:", e
+		print("cant get system keyboard repeat delay/rate:", e)
 	pygame.key.set_repeat(repeat_delay, 1000/repeat_rate)
 	pygame.time.set_timer(pygame.USEREVENT, 777) #poll for SIGINT once in a while
 
--- nodes.py	(original)
+++ nodes.py	(refactored)
@@ -233,7 +233,7 @@
 
 		#results of eval
 		if "value" in elem.runtime._dict \
-				and elem.runtime._dict.has_key("evaluated") \
+				and "evaluated" in elem.runtime._dict \
 				and not isinstance(elem.parent, Parser): #dont show results of compiler's direct children
 			yield [ColorTag('eval results'), TextTag("->")]
 			v = elem.runtime.value
@@ -288,8 +288,8 @@
 	def serialize(s):
 		r = {}
 		log("serializing Unresolved with data:", s.data)
-		for k,v in s.data.iteritems():
-			if isinstance(v, (unicode, str)):
+		for k,v in s.data.items():
+			if isinstance(v, str):
 				r[k] = v
 			elif k == "decl":
 				r[k] = v.name
@@ -378,7 +378,7 @@
 
 		assert(len(kids) == len(self.slots))
 
-		for k in self.slots.iterkeys():
+		for k in self.slots.keys():
 			self.set_child(k, kids[k])
 
 		self.ch._lock()
@@ -394,7 +394,7 @@
 		return r
 
 	def fix_parents(self):
-		self._fix_parents(self.ch._dict.values())
+		self._fix_parents(list(self.ch._dict.values()))
 
 	def set_child(self, name, item):
 		assert(isinstance(name, str))
@@ -405,9 +405,9 @@
 
 	def replace_child(self, child, new):
 		"""child name or child value? thats a good question...its child the value!"""
-		assert(child in self.ch.itervalues())
+		assert(child in iter(self.ch.values()))
 		assert(isinstance(new, Node))
-		for k,v in self.ch.iteritems():
+		for k,v in self.ch.items():
 			if v == child:
 				self.ch[k] = new
 				new.parent = self
@@ -417,7 +417,7 @@
 		#todo:refactor into find_child or something
 
 	def delete_child(self, child):
-		for k,v in self.ch._dict.iteritems():
+		for k,v in self.ch._dict.items():
 			if v == child:
 				self.ch[k] = self.create_kids(self.slots)[k]
 				self.ch[k].parent = self
@@ -427,14 +427,14 @@
 		#self.replace_child(child, Parser(b["text"])) #toho: create new_child()
 
 	def _flatten(self):
-		assert(isinstance(v, Node) for v in self.ch._dict.itervalues())
-		return [self] + [v.flatten() for v in self.ch._dict.itervalues()]
+		assert(isinstance(v, Node) for v in self.ch._dict.values())
+		return [self] + [v.flatten() for v in self.ch._dict.values()]
 
 	@staticmethod
 	def check_slots(slots):
 		if __debug__:
 			assert(isinstance(slots, dict))
-			for name, slot in slots.iteritems():
+			for name, slot in slots.items():
 				assert(isinstance(name, str))
 				assert isinstance(slot, (NodeclBase, Exp, ParametricType, Definition, SyntacticCategory)), "these slots are fucked up:" + str(slots)
 
@@ -474,7 +474,7 @@
 	def create_kids(cls, slots):
 		cls.check_slots(slots)
 		kids = {}
-		for k, v in slots.iteritems(): #for each child:
+		for k, v in slots.items(): #for each child:
 			#print v # and : #todo: definition, syntaxclass. proxy is_literal(), or should that be inst_fresh?
 			easily_instantiable = [b[x] for x in [y for y in ['text', 'number',
 			    'statements', 'list', 'function signature list', 'untypedvar' ] if y in b]]
@@ -559,7 +559,7 @@
 
 	def render_items(self):
 		r = []
-		for key, item in self.items.iteritems():
+		for key, item in self.items.items():
 			r += [TextTag(key), TextTag(":"), IndentTag(), NewlineTag()]
 			r += [ElementTag(item)]
 			r += [DedentTag(), NewlineTag()]
@@ -574,14 +574,14 @@
 
 	def fix_parents(self):
 		super(Dict, self).fix_parents()
-		self._fix_parents(self.items.values())
+		self._fix_parents(list(self.items.values()))
 
 	def _flatten(self):
-		return [self] + [v.flatten() for v in self.items.itervalues() if isinstance(v, Node)]#skip Widgets, for Settings
+		return [self] + [v.flatten() for v in self.items.values() if isinstance(v, Node)]#skip Widgets, for Settings
 
 	def add(self, kv):
 		key, val = kv
-		assert(not self.items.has_key(key))
+		assert(key not in self.items)
 		self.items[key] = val
 		assert(isinstance(key, str))
 		assert(isinstance(val, element.Element))
@@ -1227,7 +1227,7 @@
 	def __init__(self, instance_class, instance_syntaxes, instance_slots):
 		super(SyntaxedNodecl , self).__init__(instance_class)
 		instance_class.decl = self
-		self.instance_slots = dict([(k, b[i] if isinstance(i, str) else i) for k,i in instance_slots.iteritems()])
+		self.instance_slots = dict([(k, b[i] if isinstance(i, str) else i) for k,i in instance_slots.items()])
 		if isinstance(instance_syntaxes[0], list):
 			self.instance_syntaxes = instance_syntaxes
 		else:
@@ -1697,7 +1697,7 @@
 				text = text[0:pos -1] + text[pos:]
 				s.root.post_render_move_caret -= 1
 		else:
-			assert isinstance(text, (str, unicode)), (s.items, ii, text)
+			assert isinstance(text, str), (s.items, ii, text)
 			#print "assert(isinstance(text, (str, unicode)), ", s.items, ii, text
 			text = text[:pos] + e.uni + text[pos:]
 			s.root.post_render_move_caret += len(e.uni)
@@ -1727,7 +1727,7 @@
 		r = [AttTag("compiler body", self)]
 		for i, item in enumerate(self.items):
 			r += [AttTag("compiler item", i)]
-			if isinstance(item, (str, unicode)):
+			if isinstance(item, str):
 				for j, c in enumerate(item):
 					r += [AttTag("compiler item char", j), TextTag(c), EndTag()]
 			else:
@@ -1821,7 +1821,7 @@
 			#snap cursor to the beginning of Parser
 			s.root.post_render_move_caret -= atts['char_index']
 			return s.edit_text(0, 0, e)
-		elif isinstance(items[i], (str, unicode)):
+		elif isinstance(items[i], str):
 			if "compiler item char" in atts:
 				ch = atts["compiler item char"]
 			else:
@@ -1829,7 +1829,7 @@
 			return s.edit_text(i, ch, e)
 		elif isinstance(items[i], Node):
 			items.insert(i, "")
-			assert isinstance(items[i], (str, unicode)), (items, i)
+			assert isinstance(items[i], str), (items, i)
 			return s.edit_text(i, 0, e)
 
 	def mine(s, atts):
@@ -1989,7 +1989,7 @@
 		menu.sort(key=lambda i: i.score)
 
 		if debug:
-			print ('MENU FOR:',text,"type:",self.type)
+			print(('MENU FOR:',text,"type:",self.type))
 			[log(str(i.value.__class__.__name__) + str(i.scores._dict)) for i in menu]
 
 		menu.append(DefaultCompilerMenuItem(text))
@@ -2016,7 +2016,7 @@
 	@property
 	def score(s):
 		#print s.scores._dict
-		return sum([i if not isinstance(i, tuple) else i[0] for i in s.scores._dict.itervalues()])
+		return sum([i if not isinstance(i, tuple) else i[0] for i in s.scores._dict.values()])
 
 	def tags(self):
 		return [WidgetTag('value'), ColorTag("menu item extra info"), " - "+str(self.value.__class__.__name__)+' ('+str(self.score)+')', EndTag()]
@@ -2489,7 +2489,7 @@
 	pfn(sum, [Text("the sum of"), num_list_arg()], name = "summed")
 
 	def b_range(min, max):
-		return range(min, max + 1)
+		return list(range(min, max + 1))
 	pfn(b_range, [Text("numbers from"), num_arg('min'), Text("to"), num_arg('max')],
 		num_list(), name = "range", note="inclusive")
 
@@ -2689,7 +2689,7 @@
 	r.add(("program", b['module'].inst_fresh()))
 	r["program"].ch.statements.newline()
 	r.add(("builtins", b['module'].inst_fresh()))
-	r["builtins"].ch.statements.items = list(b.itervalues())
+	r["builtins"].ch.statements.items = list(b.values())
 	r["builtins"].ch.statements.add(Text("---end of builtins---"))
 	r["builtins"].ch.statements.view_mode = 2
 	building_in = False
@@ -2701,8 +2701,8 @@
 
 
 def to_lemon(x):
-	print ("to-lemon", x)
-	if isinstance(x, (str, unicode)):
+	print(("to-lemon", x))
+	if isinstance(x, str):
 		return Text(x)
 	elif isinstance(x, (int, float)):
 		return Number(x)
--- project.py	(original)
+++ project.py	(refactored)
@@ -131,7 +131,7 @@
 			tag = ElementTag(elem.__dict__[tag.name])
 
 	#now real stuff
-		if isinstance(tag, (str, unicode)):
+		if isinstance(tag, str):
 			for char in tag:
 				attadd(p.atts, "char_index", p.char_index)
 				if char == "\n":
--- utils.py	(original)
+++ utils.py	(refactored)
@@ -2,7 +2,7 @@
 
 def flatten_gen(x):
 	for y in x:
-		if isinstance(y, (unicode, str)) or not isinstance(y, list):
+		if isinstance(y, str) or not isinstance(y, list):
 			yield y
 		else:
 			for z in flatten_gen(y):
