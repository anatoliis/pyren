#!/bin/bash
#chmod +x ./venv/bin/activate
#chmod +x ./_pyren3_launcher.py
## Linux ubuntu fixes uncomment next lines
#printf "Install new venv ...\n"
#Install venv if not present
#python3 -m venv ./venv
#fix qt platform plugin ubuntu "xcb"
#sudo apt-get install --reinstall libxcb-xinerama0
##
#printf "Activate venv ...\n"
#./venv/bin/activate
printf "Runs app ...\n"
#./venv/bin/python ./_pyren_launcher.py
python3 ./_pyren3_launcher.py
#printf "Deactivate venv ..."
#./venv/bin/deactivate