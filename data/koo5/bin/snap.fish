#!/usr/bin/env fish
btrfs subvolume snapshot -r $argv[1]  $argv[2]/(date -u --iso-8601=seconds)
df -h  $argv[2]

