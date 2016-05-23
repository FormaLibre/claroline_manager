#/bin/bash

cd /home/fransfischer/claroline
rm -rf app/cache/*
rm -rf app/sessions/*
cd /home/bulbul/Claroline/claroline_manager
python claroline.py perm --name=fransficher -nc
