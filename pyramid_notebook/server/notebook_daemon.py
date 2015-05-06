"""Daemonized Python Notebook process with pre-allocated port."""

import sys
import json
import time
import psutil
import signal
import os

import daemonocle
from daemonocle import expose_action
from daemonocle import DaemonError

port = None
kill_timeout = None


class NotebookDaemon(daemonocle.Daemon):

    def __init__(self, **kwargs):
        super(NotebookDaemon, self).__init__(**kwargs)

    @expose_action
    def status(self):
        """Status command reports active port etc. ."""
        if self.pidfile is None:
            raise DaemonError('Cannot get status of daemon without PID file')

        pid = self._read_pidfile()
        if pid is None:
            self._emit_message(json.dumps(dict(status="stopped")))
            sys.exit(0)

        proc = psutil.Process(pid)

        port = read_port(self.pidfile)

        # Default data
        data = {
            'pid': pid,
            'status': 'running',
            'proc_status': proc.status(),
            'port': port,
        }

        self._emit_message(json.dumps(data))



def create_named_notebook(fname):
    """Create a named notebook if one doesn't exist."""

    if os.path.exists(fname):
        return

    from IPython.nbformat import current as nbf

    # Courtesy of http://nbviewer.ipython.org/gist/fperez/9716279
    text = "Welcome to pyramid_notebook shell! -Mikko, https://opensourcehacker.com"
    cells = [nbf.new_text_cell('markdown', text), nbf.new_code_cell('')]

    nb = nbf.new_notebook()
    nb['worksheets'].append(nbf.new_worksheet(cells=cells))
    with open(fname, 'w') as f:
        nbf.write(nb, f, version=4)


def get_port_file_name(pid_file):
    """When the daemon is started write out the information which port it was using."""
    new_extension = ".port"
    (root, ext) = os.path.splitext(pid_file)
    port_file = root + new_extension
    return port_file


def write_port(pid_file, port):
    port_file = get_port_file_name(pid_file)
    with open(port_file, "wt") as f:
        f.write(str(port))


def read_port(pid_file):
    port_file = get_port_file_name(pid_file)
    with open(port_file, "rt") as f:
        port = int(f.readline())
    return port


def run_notebook(foreground=False):

    # Set dead man's switch
    def kill_me(num, stack):
        """Oblig. Alien reference."""
        sys.exit(66)

    signal.signal(signal.SIGALRM, kill_me)
    signal.alarm(kill_timeout)

    argv = ["notebook"]

    assert port

    notebook_name = "default.ipynb"

    create_named_notebook(notebook_name)

    try:
        import IPython

        config = IPython.Config()

        config.NotebookApp.port = port
        config.NotebookApp.open_browser = foreground
        config.NotebookApp.file_to_run = notebook_name
        # Never returns
        ipython = IPython.start_ipython(argv=argv, config=config)

    except Exception as e:
        import traceback ; traceback.print_exc()
        sys.exit(str(e))


if __name__ == '__main__':

    if len(sys.argv) == 1:
        sys.exit("Usage: {} start|stop|status|fg pid_file [work_folder] [notebook port] [kill timeout in seconds]")

    action = sys.argv[1]
    pid_file = sys.argv[2]

    if action in ("start", "restart", "fg"):
        workdir = sys.argv[3]
        port = int(sys.argv[4])
        kill_timeout = int(sys.argv[5])

        write_port(pid_file, port)
    else:
        workdir = os.getcwd()

    if action == "fg":
        # Test run on foreground
        run_notebook(foreground=True)
    else:
        daemon = NotebookDaemon(pidfile=pid_file, workdir=workdir)
        daemon.worker = run_notebook
        daemon.do_action(action)

    sys.exit(0)