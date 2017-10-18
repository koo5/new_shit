import argparse

from lemon_utils.lemon_six import unicode

parser = argparse.ArgumentParser()
parser.add_argument('--log-parsing', action='store_true')
parser.add_argument('--graph-grammar', action='store_true')
parser.add_argument('--debug', action='store_false')
parser.add_argument('--debug-objgraph', action='store_true')
parser.add_argument('--profile', action='store_true')
#parser.add_argument('input', type=str)

args = parser.parse_args([]) # dummy for testing

def parse_args():
	global args
	args = parser.parse_args()

