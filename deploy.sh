#!/bin/bash
HOST=frame.local
set -e
rsync -av --exclude deploy.sh \
  --exclude venv/  \
  --exclude 'pictures/*.jpg' \
  --exclude __pycache__/ \
  --exclude '*/__pycache__' \
  --exclude '.git*' \
  --exclude '.env' \
  ./ $HOST:work/roFrame/
ssh $HOST sudo reboot
