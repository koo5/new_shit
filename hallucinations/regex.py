# region regexes
"""
we got drunk and wanted to implement regex input. i will hide this in its own module asap.
"""
#regex is list of chunks
#chunk is matcher + quantifier | followed-by
#matcher is:
#chars
#range
#or
"""
SyntacticCategory({'name': Text("chunk of regex")})
SyntacticCategory({'name': Text("regex quantifier")})
SyntacticCategory({'name': Text("regex matcher")})
#WorksAs.b("expression", "statement")

class Regex(Syntaxed):
	pass

SyntaxedNodecl(Regex,
	[ChildTag('chunks')],
	{'chunks': b["list"].make_type({'itemtype': Ref(b['chunk of regex'])})})

class RegexFollowedBy(Syntaxed):
	pass
SyntaxedNodecl(RegexFollowedBy,
	["followed by"],
	{})

class QuantifiedChunk(Syntaxed):
	 pass
SyntaxedNodecl(QuantifiedChunk,
	[ChildTag("quantifier"), ChildTag("matcher")],
	{"quantifier": b['regex quantifier'],
	"matcher": b['regex matcher']})

class UnquantifiedChunk(Syntaxed):
	pass
SyntaxedNodecl(UnquantifiedChunk,
	[ChildTag("matcher")],
	{"matcher": b['regex matcher']})

#i skew the grammar a bit so it will be easier to construct things in the stupid gui#kay
#normally i think it would be defined #hmm nvm

class RegexZeroOrMore(Syntaxed):
	pass
SyntaxedNodecl(RegexZeroOrMore,
	['zero or more'],{})

class RegexChars(Syntaxed):
	pass
SyntaxedNodecl(RegexChars,
	[ChildTag("text")],
	{'text': b['text']})
class RegexRange(Syntaxed):
	pass
SyntaxedNodecl(RegexRange,
	['[', ChildTag("text"), ']'],
	{'text': b['text']})



def b_match(regex, text):
	import re
	#...

BuiltinPythonFunctionDecl.create(
	b_match, 
	[
	Text('number of matches of'),
	TypedParameter({'name': Text('regex'), 'type':Ref(b['regex'])}),
	Text('with'), 
	TypedParameter({'name': Text('text'), 'type':Ref(b['text'])})],
	Ref(b['number']), #i should add bools and more complex types........
	"match",
	"regex")
"""

"""
Quantifiers
'a?' : 'a' 0 or 1 times
'a*' : 'a' 0 or more times
'a+' : 'a' 1 or more times
'a{9}': 2 'a's
'a{2, 9}': between 2 and 9 'a's
'a{2,}' : 2 or more 'a's
'a{,5}' : up to 5 'a's

Ranges:
'[a]': 'a'
'[a-z]': anything within the letters 'a' to 'z'
'[0-9]': same, but with numbers
'(a)' : 'a'#group?yes#ok no groups for us for now
'(a|b|c)': 'a' or 'b' or 'c'#i think this should be kept, because i think it
is the only way to match a quantity of alternations#i see
'a|b' : 'a' or 'b' (without group)
'^a' : 'a' at start of string
'a$' : 'a' at end of string

Tah-dah!#you really like typing.
"""
