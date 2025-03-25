#!/bin/bash
HOST=$1
set -e
rsync -av --exclude deploy.sh \
  --exclude venv/  \
  --exclude 'pictures/*.jpg' \
  --exclude __pycache__/ \
  --exclude '*/__pycache__' \
  --exclude '.git*' \
  --exclude '.env' \
  --exclude '.DS_Store' \
  --exclude 'roon_*.txt' \
  ./ $HOST:work/roFrame/
#ssh $HOST sudo reboot
