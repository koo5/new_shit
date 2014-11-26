

import lemon_platform

lemon_platform.frontend = lemon_platform.server

import lemon

import collect

lemon.start()


#event -> render ->

def on_keypress(event):
	#for now, always talk to the element to the right of the cursor,
	# left is [0], right is [1]
	right = event.atts[1]
	if type(right) == dict and tags.att_node in right:
		element_id = right[tags.att_node]
		element = tags.proxied[element_id]

	#old style
	while element != None:
		assert isinstance(element, Element), (assold, element)
		if element.on_keypress(event):
			break
		assold = element
		element = element.parent


	if element != None:
	# the loop didnt end with root.parent, so some element must have handled it
		if args.log_events:
			log("handled by "+str(element))
			return True



def render_root():
	collect.collect_elem(lemon.root)