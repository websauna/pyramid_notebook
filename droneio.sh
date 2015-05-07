#!/bin/bash

set -e

# Need to upgrade to Python 3.4
sudo add-apt-repository ppa:fkrull/deadsnakes > /dev/null 2>&1
sudo apt-get -qq update > /dev/null 2>&1
sudo apt-get -qq install python3.4-dev > /dev/null 2>&1

# Creteat test virtualenv
python3.4 -m venv venv
. venv/bin/activate

# Make sure pip itself is up to date
pip install -U --quiet pip
pip install --quiet -r test-requirements.txt

# Make venv aware of our own package
python setup.py develop

sudo start xvfb

# Run tests using py.test test runner
echo "Running tests"
py.test tests/* --cov pyramid_notebook --cov-report xml --splinter-webdriver=firefox --splinter-make-screenshot-on-failure=false --ini=pyramid_notebook/demo/development.ini

# Update data to codecov.io
codecov --token="$CODECOV_TOKEN"

echo "Done with tests"
