#!/usr/bin/env bash
grep -n print $@ | grep -v "#"

