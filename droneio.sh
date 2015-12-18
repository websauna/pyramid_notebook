#!/bin/bash

set -e
set -x

# Make sure pip itself is up to date
pip install -U --quiet pip
pip install --quiet -r test-requirements.txt

# Make venv aware of our own package
python setup.py develop

sudo start xvfb

# Run tests using py.test test runner
echo "Running tests"
py.test tests/* --cov pyramid_notebook --cov-report xml --splinter-webdriver=chrome --splinter-screenshot-dir=screenshots --ini=pyramid_notebook/demo/development.ini

# Update data to codecov.io
codecov --token="$CODECOV_TOKEN"

echo "Done with tests"
