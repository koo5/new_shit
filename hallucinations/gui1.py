class Lang

class Lemon
  preamble, body =

class Slice
  cursor = 0
class Meaning

class Char
  char = "a"


def test():
  l = Lemon()
  b = l.body
  b.text_typed("banana is a kind of fruit")
  for i in range(5): b.backspace()
  b.text_typed("tropical fruit")
