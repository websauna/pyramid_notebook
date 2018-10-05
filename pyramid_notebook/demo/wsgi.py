# Standard Library
import os

# Pyramid
from pyramid.paster import get_app
from pyramid.paster import setup_logging

# Pyramid Notebook
from pyramid_notebook.demo import main  # noQA


ini_path = os.path.join(os.path.dirname(__file__), "..", "..", "uwsgi-development.ini")
setup_logging(ini_path)

application = get_app(ini_path, 'main')
