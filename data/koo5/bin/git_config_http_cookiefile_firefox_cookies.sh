#!/bin/sh
#http://surniaulula.com/2012/10/11/wget-with-firefox-cookies/

#firefox "http://vm-0.koo5.kd.io/Teamwork/new_shit/.git/"

cookie_file="`echo $HOME/.mozilla/firefox/*.default/cookies.sqlite`"
user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:15.0) Gecko/20100101 Firefox/15.0.1"

echo ".mode tabs
select host, case when host glob '.*' then 'TRUE' else 'FALSE' end,
path, case when isSecure then 'TRUE' else 'FALSE' end, 
expiry, name, value from moz_cookies;" | \
	sqlite3 "$cookie_file" > ~/firefox_cookies.txt
git config http.cookiefile ~/firefox_cookies.txt
