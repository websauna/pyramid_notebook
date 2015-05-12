import os

from pyramid.paster import get_app, setup_logging

from pyramid_notebook.demo import main

ini_path = os.path.join(os.path.dirname(__file__), "..", "..", "uwsgi-development.ini")
setup_logging(ini_path)

application = get_app(ini_path, 'main')

