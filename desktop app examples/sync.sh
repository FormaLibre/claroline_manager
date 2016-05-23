#/bin/bash

ssh-add /home/bulbul/.ssh/fransfisher_rsa
cd /home/bulbul/Claroline/claroline_manager
scp fransfischer@thor.claroline.com:/home/fransfischer/fransfischer.yml platforms/
python claroline.py param-migrate --name=fransfischer --srv=fransfischer@thor.claroline.com -nc
python claroline.py dist-migrate --name=fransfischer -nc
