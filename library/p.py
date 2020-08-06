import json,sys
j = json.load(open('xbacklight.lemon.json', 'r'))
sys.stdout.write(j['last_rendering'])
