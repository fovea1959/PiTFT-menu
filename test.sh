#!/bin/bash

errors=0

reset

cmd=`python tft-menu.py v_menu.json 2> tft-menu.log`
rv=$?
if [ $rv -ne 0 ]; then
 ((errors++))
fi

if [ $errors -eq 0 ]; then
 echo $cmd
else
 echo $errors error\(s\)
 cat < tft-menu.log
 exit $rv
fi
