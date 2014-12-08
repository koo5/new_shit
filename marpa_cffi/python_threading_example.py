#!/usr/bin/env python3

# this is an illustration of sequential, that is, nonconcurrent, threading

from threading import Thread

data = [1,2,3,4]

def mess_with_data():
	data.append(5)

def do_other_things_with_data():
	data.pop()


t1 = Thread(target=mess_with_data)
t1.start()
t1.join() # waits for t1 to finish

do_other_things_with_data() # nobody else is touching my data now,
# so i can do anything with them
