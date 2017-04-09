class Lang

class Lemon
  preamble, body =

class Slice
  cursor = 0
class Binary

class Char
  char = "a"


def test():
  l = Lemon()
  b = l.body
  b.text_typed("banana is a kind of fruit")
  for i in range(5): b.backspace()
  b.text_typed("tropical fruit")





class Base(Lang)
  """
  resources:
  https://github.com/linkeddata/swap/blob/master/grammar/ebnf.rdf
  https://github.com/kenda/nlp2rdf.MontyLingua/blob/master/penn-syntax/BNF.rdf
  http://dig.csail.mit.edu/breadcrumbs/node/85
  """