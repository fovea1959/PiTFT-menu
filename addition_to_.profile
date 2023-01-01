TTY=`tty`
echo tty is $TTY, path is $PATH
if [[ "$TTY" == "/dev/tty1" ]]; then
 echo Console
 $HOME/bin/tft-menu.sh $HOME/bin/tft-menu.json
else
 echo Not Console
fi
