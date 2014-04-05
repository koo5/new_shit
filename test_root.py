# -*- coding: utf-8 -*-
from nodes import *
import settings, toolbar
import the_doc

def test_root():
	r = Root()
	r.add(("programs", List(types=['program'])))

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
			
			#),(
			
			#),
			
			#),(
			
			#"gridtest",Grid(
			#	items = 'notes/items',
			#	grid = [
			#	[0,1,2,3],
			#	[4,5,6,None]])
			
			#),(
			
			#(

	r.add(("modules", List(types = ['module'])))

	syntaxdefs = Module("syntaxes for builtins")
	r["modules"].add(syntaxdefs)
	syntaxdefs.add(
		SyntaxDef([t("program by "), ch("author"), t("created on "), ch("date_created"), nl(), ch("statements"), t("end."), w("run_button"), w("results")])
	)

	"""
					Module(Statements(['all'],
						[NodeTypeDeclaration(x) for x in [
							Text, Number, Dict, List, CollapsibleText, Statements,
							VariableReference, Placeholder, Clock, SyntaxDef,
							Program, Module, ShellCommand,
							Root, While, Note, Todo, Idea]]
					), name = "builtins"),
	"""

	stuff = Module("stuff")
	[stuff.add(x) for x in [
		Note("stupid, but gotta start somewhere"),
		FunctionDefinition(
			signature = FunctionSignature([Text("disable screensaver")]),
			body = Statements([ShellCommand("xset s off")]))
		]]
	r.add(("stuff", stuff))

	"""
	docs = Module("docs")
	r["docs"].add(docs)
	docs.add(("docs", the_doc.the_doc())
	docs.add(("tools", List()))
	docs["tools"].add(x) for x in [
		toolbar.SetAllSyntaxesToZero(),
		Clock()
		#save, load
		]

	"""

	settings_mod = Dict()
	[settings_mod.add(x) for x in [
		("webos hack", widgets.Toggle(None, False)),
		("font size", settings.FontSize(18)),
		("colors", Dict()),
		("sdl key repeat", settings.KeyRepeat())]]

	[settings_mod["colors"].add(x) for x in [
		("monochrome", widgets.Toggle(None, False)),
		("invert", widgets.Toggle(None, False)),
		("background", Dict())
	]]

	"""
	settings["colors"][""]
	[
				("R", widgets.Number(None, 0, (0, 255))),
				("G", widgets.Number(None, 0, (0, 255))),
				("B", widgets.Number(None, 0, (0, 255)))], False))
		]
	"""
	r.add(("settings", settings_mod))

	r.fix_relations()
	
	return r
