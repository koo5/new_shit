import argparse

from lemon_utils.lemon_six import unicode

parser = argparse.ArgumentParser()
parser.add_argument('--eightbit', action='store_true',
			   help='try to be compatible with 8 bit color mode.')
parser.add_argument('--dontblink', action='store_true',
			   help='dont blink the cursor.')
parser.add_argument('--log-events', action='store_true',
			   help='what it says.')
parser.add_argument('--noalpha', action='store_true',
			   help='avoid alpha blending')
parser.add_argument('--mono', action='store_true',
			   help='no colors, just black and white')
parser.add_argument('--webos', action='store_true',
			   help='webos keys hack')
parser.add_argument('--invert', action='store_true',
			   help='invert colors')
parser.add_argument('--replay', action='store_true')
parser.add_argument('--lesh', action='store_true')
parser.add_argument('--font-size', type=int,
			   default=22)
parser.add_argument('--load', type=unicode,
			   default=False)
parser.add_argument('--run', type=unicode,
			   default=False)
parser.add_argument('--log-height', type=int,
				default=4)
parser.add_argument('--lame', action='store_true')
parser.add_argument('--log-parsing', action='store_true')
parser.add_argument('--graph-grammar', action='store_true')
parser.add_argument('--debug', action='store_false')
parser.add_argument('--debug-objgraph', action='store_true')
parser.add_argument('--rpc', action='store_true')
parser.add_argument('--root', action='store_true')
parser.add_argument('--menu', action='store_true')
parser.add_argument('--intro', action='store_true')
parser.add_argument('--profile', action='store_true')
parser.add_argument('--no-timers', action='store_true')


parser.add_argument('--freetype', dest='freetype', action='store_true')
parser.add_argument('--no-freetype', dest='freetype', action='store_false')
parser.set_defaults(freetype=True)



args = parser.parse_args([]) # dummy for testing

def parse_args():
	global args
	args = parser.parse_args()

