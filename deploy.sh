#!/bin/bash
set -e
rsync -av --exclude deploy.sh \
  --exclude venv/  \
  --exclude 'pictures/*.jpg' \
  --exclude __pycache__/ \
  --exclude '*/__pycache__' \
  --exclude '.git*' \
  --exclude '.env' \
  ./ frame.local:work/roFrame/
ssh $HOST sudo reboot
