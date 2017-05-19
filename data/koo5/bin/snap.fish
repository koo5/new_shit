#!/usr/bin/env fish
btrfs subvolume snapshot -r /home/kook/ /home/snapshots/(date -u --iso-8601=seconds)
echo "ok"
df -h /home/kook

