import pickle

import logging
logger=logging.getLogger("root")
log=logger.debug


from frontend_events import *

replay_input_event = 666 # set from sdl_client

# debug replay is cleared if first event isnt an F2 keypress so we need to track if this is the first event after program start

we_are_replaying = False
replay_file = "replay.pickle"
_ignored = False # ignore the next event passed to add() as its the key that invoked replay
is_first_input_event = True

def add(e):
	global is_first_input_event, _ignored
	#log((is_first_input_event, _ignored))
	if is_first_input_event and not _ignored:
		clear_replay()
	with open(replay_file, "ab") as f:
		try:
			log("pickling:%s",e)
			pickle.dump(e, f)
		except pickle.PicklingError as error:
			log("%s, are you profiling? (%s)", error, e)
	is_first_input_event = _ignored = False


def clear_replay():
	log("clearing replay..")
	f = open(replay_file, 'w')
	f.truncate()
	f.close()



def do_replay(invoked_interactively = True):
	global we_are_replaying, _ignored
	if invoked_interactively:
		_ignored = True
	if we_are_replaying:
		log("already replaying")
		return
	try:
		with open(replay_file, "rb") as f:
			info("replaying...")
			we_are_replaying = True
			while 1:
				try:
					e = pickle.load(f)
				except EOFError:
					break
				log(e)
				replay_input_event(e)
	except IOError as e:
		info("couldnt open replay.p",e)
	finally:
		we_are_replaying = False
