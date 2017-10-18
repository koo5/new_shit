#!/usr/bin/env fish

set hmmdir (dirname (status --current-filename))
set snippetsdir "$hmmdir/snippets"

if [ "$argv[1]" = "hmm" ]
	echo "updating autocompletions with $snippetsdir"
	for i in (ls $snippetsdir);
		echo $i;
		complete -xc hmm -a $i --description (cat "$snippetsdir/$i");
	end
else
	set snip "$snippetsdir/$argv[1]"
	if test -e $snip
		. $snip
	else
		echo $argv
		echo "wats $snip?"
	end
end

