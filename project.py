def squash(a):
	r = {}
	for i in a:
		r[i.items()[0][0]] = i.items()[0][1]
	return r

def test_squash():
	if squash([{"a": 1}, {"b": 2}, {"a": 3}]) != {"a": 3, "b": 2}:
		raise Exception()

def project(tags):
	lines = [[]]
	atts = []
	do_indent = True
	for tag in tags:
		if isinstance(tag, AttTag):
			atts.push(tag.attribute)
		if isinstance(tag, NodeTag):
			atts.push({"node": tag.node})
		if isinstance(tag, EndTag):
			atts.pop()
        if isinstance(tag, IndentTag):
            indent+=1
        if isinstance(tag, DedentTag):
            indent-=1

		if isinstance(tag, TextTag):
			for i, char in enumerate(tag.text):
				atts.append({"char_index": i})
				out.append((char, squash(atts)))
				atts.pop() #char_index
	return out

def break_at_newlines(self, chars):
	l = 0
	c = 0
	while c < len(chars):
		lines[l].append(chars[c])
		if chars[c] == "\n":
			lines.append([])
			l += 1

aand this
		if self.do_indent:   
			self._append(self.indent_spaces(), a)
		self.do_indent = (text == "\n")
		self._append(text, a)


test_project():
	tags = [#output of root.render() will look something like that:  
		NodeTag(1),
		TextTag("program Hello World:"),
		IndentTag(),
		NodeTag(2),
		TextTag("print "),
		NodeTag(3),
		TextTag("\"hello world\""),
		EndTag(),
		EndTag(),
		DedentTag(),
		TextTag("end."),
		EndTag()
	]
	
	lines = project(tags)
	

def render(lines):
	for l, line in enumerate(screen):
		for c, char in enumerate(line);
			#render char on screen
