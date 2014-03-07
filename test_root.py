# -*- coding: utf-8 -*-
from nodes import *
import settings, toolbar
import the_doc

def test_root():
	r = Root(Dict([
			(
#			"placeholder test", Statements([Placeholder(types = [Node]),Placeholder(types = [Node])])
#			),(
#			"text widget test", widgets.Text(None, "Test me out!")
#			),(
#			"intro", Text("""hello...""")
#			),(
			"toolbar", List(
				[
				toolbar.SetAllSyntaxesToZero(),
				Clock()
				#save, load
				], False)
			),(
			"settings", Dict([
				("webos hack", widgets.Toggle(None, False)),
				("font size", settings.FontSize(18)),
				#("fullscreen", widgets.Toggle(None, False)),
				#("projection_debug", widgets.Toggle(None, True)),
				("invert colors", widgets.Toggle(None, False)),
				("background color", Dict([
					("R", widgets.Number(None, 0, (0, 255))),
					("G", widgets.Number(None, 0, (0, 255))),
					("B", widgets.Number(None, 0, (0, 255)))])),
				("sdl key repeat", settings.KeyRepeat()),
				], False)
			),(
			"programs", List([
				Program(Statements([
					Placeholder([], "statement")#,
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
						
				]), "hello world2", "koo5")]) #semanticize koo5:)
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
			),(
			"modules", List([
			
				Module(Statements([
					SyntaxDef([t("program by "), ch("author"), t("created on "), ch("date_created"), nl(), ch("statements"), t("end.")])
				]), name = "syntaxes for builtins"),
				
				#Module(Statements(builtins()), name = "builtins"),

				Module(Statements([
					Note("stupid, but gotta start somewhere"),
					FunctionDefinition(
						syntax = SyntaxDef([t("disable screensaver")]), 
						body = Statements([ShellCommand("xset s off")]))
				]), name = "some functions")
				
			], False)
			),(
			"docs", the_doc.the_doc()
			)
			]))
	
	for p in r.children['items'].items["programs"]: #the Program objects
		p.syntax_def = r.children['items'].items['modules'][0].children['statements'][0]
	
	r.fix_relations()
	
	return r
#prototypes?

def builtins():
	#todo:define the tree structure here
	return [NodeTypeDeclaration(x) for x in [
			Text, Number, Dict, List, CollapsibleText, Statements,
			VariableReference, Placeholder, Clock, SyntaxDef,
			Program, Module, FunctionDefNode, ShellCommand,
			Root, While, Note, Todo, Idea]]



def mini_test_root():
	return Root(Dict([
			(
			"test", widgets.Text("banana", "Test me out!")
			)]))

	


