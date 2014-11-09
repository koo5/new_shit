from lemon_logger import log

def gen_graph(root):
	try:
		import pydot
	except Exception as e:
		log(str(e))
		log("cant generate graph")
		return

	nodes = root.flatten()
	#print nodes
	#from compiler.ast import flatten
	#nodes = flatten(nodes)

	graph = pydot.Dot(graph_type='digraph')

	for node in nodes:
		graph.add_node(pydot.Node(str(node),
	                          #style="filled",
	                          #fillcolor="green",
	                          fontcolor="black"))

	for node in nodes:
		parent = node.parent
		if parent in nodes:
			graph.add_edge(pydot.Edge(str(parent), str(node), color="black"))

	graph.set_rankdir("LR")
	graph.write_gif("graph.gif")
	log("graph.gif written")
