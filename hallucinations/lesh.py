
# region lesh
class Lesh(Node):
	"""just another experiment: independent of the lemon language,
	this is a command line that calls bash to execute commands.
	a variation on shell snippets for fish / betty
	lemon would probably make it more natural to have to option to insert
	either raw text or a "human" snippet form, like <count lines>,
	and toggle them freely
	"""
	#might add history later or xiki style?
	def __init__(s):
		super(Lesh, s).__init__()
		s.command_line = LeshCommandLine()
		s.command_line.parent = s

	def on_keypress(self, e):
		if e.key == K_RETURN:
			import os
			cmd = ''.join(self.command_line.items)
			log("running "+cmd+":", os.system(cmd))
			return True


	def render(self):
		return [TextTag("just a little experiment, a frontend for bash/fish/zsh that lets you insert snippets and stuff:\n"),
		                MemberTag('command_line')]

class LeshSnippetDeclaration(Syntaxed):
	"""a declaration of a snippet"""
	def __init__(self, children):
		super(LeshSnippetDeclaration, self).__init__(children)
	@property
	def human(s):
		return s.ch.human.pyval
	@property
	def command(s):
		return s.ch.command.pyval

	def palette(self, scope, text, node):
		return [LeshMenuItem(self)]


if False:#args.lesh:

	build_in(SyntaxedNodecl(LeshSnippetDeclaration,
					[[ChildTag("human"), ChildTag("command")]],
					{'human': b['text'], #add more wordings later
					'command': b['text']}))

	for h,c in [
		("count words", "wc"),
		("mount all", "mount -a")

		]:
			build_in(LeshSnippetDeclaration({'human':Text(h), 'command':Text(c)}), False)

class LeshSnippet(Node):
	"""for the case you want to insert the snippet in the human readable form"""
	def __init__(self, declaration):
		super(LeshSnippet, self).__init__()
		self.declaration = declaration

#todo: alt insert mode
#todo: split on pipes
# endregion


# region lesh command line

class LeshCommandLine(ParserBase):
	def __init__(self):
		super(LeshCommandLine, self).__init__()

	def empty_render(s):
		return []

	@topic("lesh menu")
	def menu_for_item(self, i=0, debug = False):

		if i == None:
			if len(self.items) == 0:
				text = ""
			else:
				return []
		else:
			if isinstance(self.items[i], Node):
				text = ""
			else:
				text = self.items[i]

		scope = self.root["builtins"].ch.statements.parsed
		menu = flatten([x.palette(scope, text, self) for x in scope if isinstance(x, LeshSnippetDeclaration)])

		matchf = fuzz.token_set_ratio#partial_ratio

		for item in menu:
			v = item.value
			item.scores.human = matchf(v.human, text), v.human #0-100
			item.scores.command = matchf(v.command, text), v.command#0-100

		menu.sort(key=lambda i: i.score)

		menu.append(DefaultParserMenuItem(text))
		menu.reverse()

		return menu


	def menu_item_selected_for_child(self, item, child_index, char_index, alt=False):
		assert isinstance(item, (LeshMenuItem, DefaultParserMenuItem))
		if isinstance(item, LeshMenuItem):

			dec = item.value

			if alt:
				snippet = LeshSnippet(dec)
			else:
				snippet = dec.command

			if child_index != None:
				orig = self.items[child_index]
				if isinstance(orig, unicode):
					self.items = insert_between_pipes(snippet, char_index, child_index, self.items)
				#self.items[child_index] = snippet
			else:
				self.items.append(snippet)

			if alt:
				snippet.parent = self
			#self.post_insert_move_cursor(node)
			return True

		elif isinstance(item, DefaultParserMenuItem):
			return False
		else:
			raise Exception("whats that shit, cowboy?")

def cut_off_until(s, at):
	for i,c in enumerate(s):
		if c == at:
			return s[i:]
	return ""

def rcut_off_until(s, at):
	for i,c in reversed(list(enumerate(s))):
		if c == at:
			return s[:i+1]
	return ""

def test_cut_off_until():
	testres = cut_off_until("cat x | y | z", "|")
	testexp = "| y | z"
	assert testres == testexp, (testres, testexp)

	testres = cut_off_until("cat x  y  z", "|")
	testexp = ""
	assert testres == testexp, (testres, testexp)

	testres = cut_off_until("", "|")
	testexp = ""
	assert testres == testexp, (testres, testexp)

	testres = rcut_off_until("", "|")
	testexp = ""
	assert testres == testexp, (testres, testexp)

	testres = rcut_off_until("cat x | y | z", "|")
	testexp = "cat x | y |"
	assert testres == testexp, (testres, testexp)

	testres = rcut_off_until("cat x  y  z", "|")
	testexp = ""
	assert testres == testexp, (testres, testexp)

test_cut_off_until()

def insert_between_pipes(snippet, char_index,item_index, items):
	"""if there are |'s in the replaced item, we want to split it in two or three parts,
	and put the replacement in the middle
	thats what you would want when editing a bit of bash...hmm
	the lesh command line is technically text, id just rather work on something
	that benefits both lemon and lesh, because this is ultimately about the sweet spot
	between structured and textual editing. yeah
	"""
	delim = "|"
	orig = items[item_index]
	left,right = orig[:char_index], orig[char_index:]
	#print (left,right)
	left,right = rcut_off_until(left,delim),cut_off_until(right,delim)
	r = items[:item_index]
	if left != "":
		r.append(left)
	r.append(snippet)
	if right != "":
		r.append(right) #im back, sorry, chromium had a memory leak and i had to reboot.hey
	r += items[item_index+1:]
	return r

#the Parser works with a list of items, they can be strings or Nodes
#how or why is for a longer debate...


def test_insert_between_pipes():
	testres = insert_between_pipes(
		'fart', #replacement item selected from menu
		0, #this should be the index of the char of the item
		7, #this is the index of the item on which the cursor is, we are replacing this item
		[0,1,2,3,4,5,6,"cat x | count words | sum",8,9]) #this is the current items
	#"cat x | count words | sum" is what you have on the command line,
	#you typed "count words" between two pipes, and selected wc #mm
	#what complicates this as compared to normal lemon Parser is umm...this!
	testexp = [0,1,2,3,4,5,6,"fart", "| count words | sum",8,9]
	assert testres == testexp, (testres, testexp)

	testres = insert_between_pipes('fart', 6, 0, ["cat x | count words | sum"]) #you know, the gnu code standard says to put parentheses around stuff that doesnt really need it so emacs will indent it properly hmm no? just saying ok
	testexp = ["fart", "| count words | sum"]
	assert testres == testexp, (testres, testexp)

	testres = insert_between_pipes('fart', 7, 0, ["cat x | count words | sum"])
	testexp = ["cat x |", "fart", "| sum"]
	assert testres == testexp, (testres, testexp)

test_insert_between_pipes()

class LeshMenuItem(MenuItem):
	#hack
	def __init__(self, snippet, score = 0):
		super(LeshMenuItem, self).__init__()
		self.value = snippet
		self.scores = Dotdict()
		self.brackets_color = (0,255,255)

	@property #duplicate...
	def score(s):
		return sum([i if not isinstance(i, tuple) else i[0] for i in itervalues(s.scores._dict)])

	def tags(self):
		return [self.value.human, ":\n", self.value.command]

# endregion

