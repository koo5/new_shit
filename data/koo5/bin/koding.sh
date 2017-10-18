mkdir ~/x
cd ~/x
vncserver :1
~/noVNC/utils/websockify --web ./ 8787 localhost:5901
