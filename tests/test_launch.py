import random
import time

from pyramid_notebook.launcher import Launcher
import psutil


TEST_PYTHON = "python3.4"


def test_spawn():
    """Create a Python process."""

    # Construct a Python process which runs 10 seconds
    arg_factory = lambda: ["-c", "import time ; time.sleep(10)"]

    tag = "-W={}".format(random.randint(0, 1000000))

    l = Launcher(TEST_PYTHON, tag, arg_factory=arg_factory)

    proc, created = l.get_or_spawn_process()
    assert created

    # Should not die immediately
    time.sleep(1)
    assert psutil.pid_exists(proc.pid), "PID created, but died immediately "

    proc.kill()
    time.sleep(1)
    assert not proc.is_running(), "Could not kill {}".format(proc)



def test_find_existing():
    """Find existing process and don't launch duplicate."""

    arg_factory = lambda: ["-c", "import time ; time.sleep(10)"]
    tag = "-W={}".format(random.randint(0, 1000000))
    l = Launcher(TEST_PYTHON, tag, arg_factory)

    proc, created = l.get_or_spawn_process()
    assert created

    # Should not die immediately
    time.sleep(1)
    assert psutil.pid_exists(proc.pid)

    # Find existing one
    proc2, created = l.get_or_spawn_process()
    assert not created
    assert proc.pid == proc2.pid



