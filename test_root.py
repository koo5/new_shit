# -*- coding: utf-8 -*-
from nodes import *
import settings, toolbar

def test_root():
	r = Root()
	r.add(("programs", List(types=['program'])))
	r["programs"].add(Program())
	r["programs"][0].ch.statements.newline()
	#r["programs"].add(
				#Program(Statements([
					#Placeholder([], "statement")#,
					#FunctionDefinition(name = Text("substring")),
					#Asignment(Text("a"), Number(1)),
					#Asignment(Text("b"), Number(5)), 
					#While(IsLessThan(VariableRead("a"), VariableRead("b")),	Statements([
					#	Print(
					#		VariableRead("a")), #byname
					#		Placeholder()])),
					#laceholder()]), name="test1"),
					#If(IsLessThan(VariableRead("a"), Number(4)),
					#	Statements([Print(Text("hi!\n"))]))
				#	For(VariableDeclaration("item")
				#]), "hello world2", "koo5")]) #semanticize koo5:)
			
	r.add(("modules", List(types = ['module'])))

	syntaxdefs = Module("syntaxes for builtins")
	r["modules"].add(syntaxdefs)
	syntaxdefs.add(
		SyntaxDef([t("program by "), ch("author"), t("created on "), ch("date_created"), nl(), ch("statements"), t("end."), w("run_button"), w("results")])
	)

	r["modules"].add(nodes.builtins)

	stuff = Module("stuff")
	[stuff.add(x) for x in [
		Note("stupid, but gotta start somewhere"),
		FunctionDefinition(
			signature = FunctionSignature([Text("disable screensaver")]),
			body = Statements([ShellCommand("xset s off")]))
		]]
	r.add(("stuff", stuff))
	"""

	r.fix_parents()
	
	return r
