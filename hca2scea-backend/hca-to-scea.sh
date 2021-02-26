#!/bin/bash

echo "[HCA-TO-SCEA SH LAUNCHER] ACTIVATING VIRTUALENV"
source ./venv/bin/activate

echo "[HCA-TO-SCEA SH LAUNCHER] LAUNCHING SCRIPT"
./hca-to-scea.py $1 $2
