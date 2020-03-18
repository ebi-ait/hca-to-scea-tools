#!/bin/bash

npm install

virtualenv venv --python=/usr/bin/python3.7
source ./venv/bin/activate

pip install -r requirements.txt

deactivate

echo Ready. To start the tool, run \`npm start\ and point a browser to `
https://www.udemy.com/course/react-2nd-edition/
