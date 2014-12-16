import pickle

from lemon_utils.lemon_logging import log

# debug replay is cleared if first event isnt an F2 keypress so we need to track if this is the first event after program start
is_first_input_event = True

def pickle_event(e):
	global is_first_input_event
	if is_first_input_event:
		clear_replay()
	with open("replay.pickle", "ab") as f:
		try:
			pickle.dump(e, f)
		except pickle.PicklingError as error:
			log(error, ", are you profiling?")
	is_first_input_event = False

def clear_replay():
	f = open("replay.p", 'w')
	f.truncate()
	f.close()



def do_replay(ff):
	global fast_forward
	try:
		with open("replay.p", "rb") as f:
			log("replaying...")
			if ff:
				fast_forward = True #ok, not much of a speedup. todo:dirtiness
			while 1:
				try:
					e = pickle.load(f)
					log(str(e))
					if e.type == KEYDOWN:
						keypress(e)
					elif e.type == MOUSEBUTTONDOWN:
						mousedown(e)
					else:
						raise Exception("unexpected event type:", e)
					render()
					if not fast_forward:
						draw()

				except EOFError:
					break

			fast_forward = False

	except IOError as e:
		log("couldnt open replay.p",e)

