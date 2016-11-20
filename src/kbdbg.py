
class Kbdbg(Node):
	def __init__(s):
		super(Kbdbg, s).__init__()
		s.isroot = True
		s.parent = None
		s.decl = None
		s.delayed_cursor_move = DelayedCursorMove()
		s.indent_length = 4
		s.changed = True
		s.brackets = ("", "")
		s.items = []
		s.arrows = []
		s.loadkb()
		print (Kbdbg.keys)
		s.update()

	def render(s):
		yield ColorTag(colors.fg)
		print ("RENDER")
		yield s.items
		yield EndTag()

	def update(s):
		#for a in s.arrows:
			#print (a)
		print ("UPDATE")

		s.items.clear()
		for i in s.kb:
			#print(i.markup)
			if len(i.markup) != 0:
				for a in s.arrows:
					if i.markup == a[0]["markup"]:
						#print ("OOO", i.markup, "FFF", a[0]["markup"])
						for j in s.kb:
							#print("XXX",  j.markup, a[1]["markup"])
							if j.markup == a[1]["markup"]:
								style = a[2]
								s.items.append(ArrowTag(j, style))
								s.items.append("o")
					#if i.markup == a[1]["markup"]:
					#	s.items.append("x")


			s.items.append(ElementTag(i))

	def add_step(s):
		print("adding step")
		s.steps.append(Dotdict())
		s.steps[-1].log = []
		s.steps[-1].vis = []

	def loadkb(s):

		s.steps = []
		s.add_step()
		input = json.load(open("kbdbg.json", "r"))
		s.kb = []
		for i in input:
			if isinstance(i, dict):
				#print (i)
				if i["type"] == "step":
					s.add_step()
				else:
					s.steps[-1].vis.append(i)
			elif isinstance(i, unicode):
				s.steps[-1].log.append(i)
			elif isinstance(i, list):
				for x in i:
					if isinstance(x, str):
						t = x
						m = []
					elif isinstance(x, dict):
						t = x["text"]
						m = x["markup"]
					w = widgets.Text(s, t)
					w.markup = m
					s.kb.append(w)

		s.arrows = []
		s.cache = {}
		s.step = -1
		s.step_fwd()

	def print_log(s):
		for line in s.steps[s.step].log:
			print(line)

	def step_back(s):

		if s.step != 0:
			s.step -= 1
		s.arrows = copy(s.cache[s.step])
		s.update()
		if s.step == 0:
			print()
			print()
			print()
			print()
			print("START")
			print()
			print()
			print()

		print ("step:", s.step)
		s.print_log()

	def step_fwd(s):

		if s.step < len(s.steps) -1 :
			s.step += 1
			if s.step in s.cache:
				s.arrows = copy(s.cache[s.step])
			else:
				s.do_step(s.step)
				s.cache[s.step] = copy(s.arrows)
			s.update()
		print ("step:", s.step)
		s.print_log()

	def do_step(s, i):

		for x in s.steps[i].vis:
			print(x)
			p = (x["a"], x["b"], x["style"])
			if x["type"] == "add":
				print("add" , p)
				s.arrows.append(p)
			elif x["type"] == "remove":
				for y in range(len(s.arrows)):
					if s.arrows[y] == p:
						print("remove" , p)
						s.arrows.remove(p)
						break
			else:
				assert(False)


	def has_result(s):
		for line in s.steps[s.step].log:
			if line[:6] == "RESULT":
				return True


	def res_back(s,e):
		while s.step != 0:
			s.step_back()
			if s.has_result(): return

	def res_fwd(s,e):
		while s.step < len(s.steps) -1 :
			s.step_fwd()
			if s.has_result(): return

