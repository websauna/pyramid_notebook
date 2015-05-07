import logging
import os
import time
import random

from pyramid_notebook.notebookmanager import NotebookManager


NOTEBOOK_FOLDER = os.path.join("/tmp", "pyramid_notebook_tests")
os.makedirs(NOTEBOOK_FOLDER, exist_ok=True)

logging.basicConfig(level=logging.DEBUG)

USER = "testuser1"


def test_spawn():
    """Create a Python Notebook process."""

    m = NotebookManager(notebook_folder=NOTEBOOK_FOLDER, kill_timeout=60)

    m.start_notebook(USER, None, fg=False)
    time.sleep(1)
    status = m.get_notebook_status(USER)
    assert type(status) == dict
    assert status["pid"] > 0
    assert status["http_port"] > 0

    m.stop_notebook(USER)
    time.sleep(1)
    status = m.get_notebook_status(USER)
    assert status is None, "Still had content in {}".format(m.get_pid(USER))




def test_context_change():
    """Check that if the context changes we launch the notebook with new parametrers."""

    m = NotebookManager(notebook_folder=NOTEBOOK_FOLDER, kill_timeout=60)

    notebook_context = {"context_hash": "123"}

    context, created = m.start_notebook_on_demand(USER, notebook_context)
    assert created
    status = m.get_notebook_status(USER)
    old_pid = status["pid"]

    # Restart with same hash
    context, created = m.start_notebook_on_demand(USER, notebook_context)
    assert not created
    status = m.get_notebook_status(USER)
    assert status["pid"] == old_pid

    # Restart with different hash
    notebook_context = {"context_hash": "456"}
    context, created = m.start_notebook_on_demand(USER, notebook_context)
    assert created
    status = m.get_notebook_status(USER)
    assert old_pid != status["pid"]

    m.stop_notebook(USER)
    time.sleep(1)
    status = m.get_notebook_status(USER)
    assert status is None, "Still had content in {}".format(m.get_pid(USER))


