<?php
$f = file_get_contents("#zennet.log");
$x = substr($f, -1024*50);
echo($x);
?>
