def tracefunc(frame, event, arg, indent=[0]):
      if event == "call":
          indent[0] += 1
          print ("-" * indent[0] + "> ", frame.f_code.co_name)
      elif event == "return":
          print ("<" + "-" * indent[0], "<", frame.f_code.co_name)
          indent[0] -= 1
      return tracefunc

import sys
sys.settrace(tracefunc)

import sdl_client

