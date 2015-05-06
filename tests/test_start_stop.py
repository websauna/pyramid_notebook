import logging
import os
import time

from pyramid_notebook.notebookmanager import NotebookManager


NOTEBOOK_FOLDER = os.path.join("/tmp", "pyramid_notebook_tests")
os.makedirs(NOTEBOOK_FOLDER, exist_ok=True)

logging.basicConfig(level=logging.DEBUG)


def test_spawn():
    """Create a Python Notebook process."""

    m = NotebookManager(notebook_folder=NOTEBOOK_FOLDER, kill_timeout=5)

    m.start_notebook("test")
    time.sleep(1)
    status = m.get_notebook_status("test")
    assert status["status"] == "running"

    m.stop_notebook("test")



def test_get_port():
    """Get port of existing running Python Notebook."""

    m = NotebookManager(notebook_folder=NOTEBOOK_FOLDER, kill_timeout=5)

    m.start_notebook("test")
    status = m.get_notebook_status("test")
    assert status["port"] >= 40000
    assert status["port"] <= 40010

    m.stop_notebook("test")







