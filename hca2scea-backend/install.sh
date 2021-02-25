#!/bin/bash

npm install

#virtualenv venv # rays22: this does not work for me 2021-02-25
python3 -m venv venv && echo 'Creating venv.'
source ./venv/bin/activate && echo 'Activating venv.'

pip install -r requirements.txt

deactivate && echo 'Deactivating venv.'

echo 'Ready. To start the tool, run `npm start` and point a browser to `127.0.0.1:5000`'

