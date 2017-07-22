#!/usr/bin/env fish
./snaploop.py 555 /home/kook /home/snapshots&
sudo -u kook ./screenshot-whole-loop.py /home/kook/screenshots
