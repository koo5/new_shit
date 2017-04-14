#!/usr/bin/env bash
killall htop synapse Telegram
ifconfig virbr0 down
service lxc stop
service mysql stop
service postgres stop
service apache2 stop
rmmod iwldvm iwlwifi hp-wmi
killall docker ntpd mission-control-5 goa-daemon goa-identity-service  postgres thunderbird cups-browsed  cron  ofonod  cupsd apache2
powertop --auto-tune
