# Standard Library
import logging
import os
import sys
import time

# Pyramid Notebook
from pyramid_notebook.notebookmanager import NotebookManager


NOTEBOOK_FOLDER = os.path.join("/tmp", "pyramid_notebook_tests")
os.makedirs(NOTEBOOK_FOLDER, exist_ok=True)

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

USER = "testuser1"


def test_spawn():
    """Create a Python Notebook process."""

    m = NotebookManager(notebook_folder=NOTEBOOK_FOLDER, kill_timeout=60)

    output = m.start_notebook(USER, {"context_hash": 1}, fg=False)
    time.sleep(1)

    # pid is set if the process launched successfully
    status = m.get_notebook_status(USER)
    if status is None:
        # Failure to launch, get error
        print(output)
        raise AssertionError("Could not start, context file was not created")

    assert type(status) == dict
    assert status["pid"] > 0
    assert status["http_port"] > 0

    assert m.is_running(USER)

    m.stop_notebook(USER)
    time.sleep(1)
    assert not m.is_running(USER)


def test_context_change():
    """Check that if the context changes we launch the notebook with new parametrers."""

    m = NotebookManager(notebook_folder=NOTEBOOK_FOLDER, kill_timeout=60)

    notebook_context = {"context_hash": 123}

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
    notebook_context = {"context_hash": 456}
    context, created = m.start_notebook_on_demand(USER, notebook_context)
    assert created
    status = m.get_notebook_status(USER)
    assert old_pid != status["pid"]

    m.stop_notebook(USER)
    time.sleep(1)
    assert not m.is_running(USER)
