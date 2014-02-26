# -*- coding: utf-8 -*-
from nodes import *
import settings, toolbar

def test_root():
	r = Root(Dict([
			(
			"test", widgets.Text("banana", "Test me out!")
			),(
			"menu", List(
				[
				toolbar.SetAllSyntaxesToZero()
				])#,compact = True
			),(
			"settings", Dict([
				("font_size", settings.FontSize(18)),
				("fullscreen", settings.Fullscreen()),
				("projection_debug", widgets.Toggle(None, True)),
				("invert colors", widgets.Toggle(None, False)),
				("background color", Dict([
					("R", widgets.Number(None, 0)),
					("G", widgets.Number(None, 30)),
					("B", widgets.Number(None, 0))])),
				("sdl key repeat", settings.KeyRepeat()),

				
					
				])
			),(
			"programs", List([
				Program(Statements([
					Placeholder()#,
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
						
				]))])
			),(
			"notes", List([
				Todo("""big themes: 
voice recognition (samson?)
eye tracking


"""),
				Todo("procrastinate more"),
				CollapsibleText(
					"""
<AnkhMorporkian_> it's probably a bad idea to have newline as its own class. it'd be better to maintain it in the document class, since you have to have that anyways when you're using it.
<AnkhMorporkian> i understand why the nodes handle their own rendering, but I don't see why simple text characters should be.
<sirdancealot_> i wanted to have it uniform, to avoid special handling of str inside the template render
					"""),

				CollapsibleText(
					"""
#couple options:
	store the positions of characters in an array ourselves - 
		hmm, this actually sounds pretty simple, might be dumping pyglets documents one day
	store positions in attributes char by char
		for everything
		for just active.. nope...clicks...
	settled for one position for each element now
					"""),
				Idea("""pick up the templating work, use an existing templating library, switch to formatted_from_text, implement functions dealing with the text with attributes if necessary"""),
				Todo("save/load nodes", priority=10),
				Todo("salvage the logger thingy...printing does get tedious...but its so damn quick")
				])
			),(
			"clock",Clock()
			),(
			"modules", List([
			
				Module(Statements([
					SyntaxDef([t("program by "), ch("author"), t("created on "), ch("date_created"), nl(), ch("statements"), t("end.")])
				]), name = "syntaxes for builtins"),

				Module(Statements([
					Note("stupid, but gotta start somewhere"),
					FunctionDefNode(
						syntax = SyntaxDef([t("disable screensaver")]), 
						body = Statements([ShellCommand("xset s off")]))
				]), name = "commands to command you PC around")
			])
			)
			]))
	
	for p in r.children['items'].items["programs"]: #the Program objects
		p.syntax_def = r.children['items'].items['modules'][0].children['statements'][0]

	return r


def mini_test_root():
	return Root(Dict([
			(
			"test", widgets.Text("banana", "Test me out!")
			)]))

	


"""


	#Что это?
	new todo list:
	systemic changes to consider:
		projectured needs to be tried out and evaluated for a possible use as the base of lemon.



"""
