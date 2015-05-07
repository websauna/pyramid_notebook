"""Daemonized Python Notebook process with pre-allocated port."""
from contextlib import redirect_stdout
import logging

import sys
import json
import time
from IPython.nbformat.v4.nbjson import JSONWriter
from IPython.nbformat.v4.rwbase import NotebookWriter
import io
import psutil
import signal
import os
import atexit

import daemonocle
from daemonocle import expose_action
from daemonocle import DaemonError
from pyramid_notebook.server import comm

port = None
kill_timeout = None
extra_argv = None
pid_file = None

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

        port = comm.read_context_info(self.pidfile)

        # Default data
        data = {
            'pid': pid,
            'status': 'running',
            'proc_status': proc.status(),
            'port': port,
        }

        self._emit_message(json.dumps(data))



def create_named_notebook(fname, context):
    """Create a named notebook if one doesn't exist."""

    if os.path.exists(fname):
        return

    from IPython.nbformat import v4 as nbf

    # Courtesy of http://nbviewer.ipython.org/gist/fperez/9716279
    text = "Welcome to pyramid_notebook shell! -Mikko, https://opensourcehacker.com"
    cells = [nbf.new_markdown_cell(text)]

    greeting = context.get("greeting")
    if greeting:
        cells.append(nbf.new_markdown_cell(greeting))

    cells.append(nbf.new_code_cell(''))

    nb = nbf.new_notebook(cells=cells)

    with open(fname, 'w') as f:
        writer = JSONWriter()
        writer.write(nb, f)



def run_notebook(foreground=False):

    # Get some debug output from IPython
    # log_file = "ipython.log"
    #logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s', datefmt='%m-%d %H:%M', filename=log_file, filemode='w')

    # logger = logging.getLogger(__name__)
    if not foreground:
        # Make it possible to follow what daemonized IPython is doing
        sys.stdout = io.open("notebook.stdout.log", "wt")
        sys.stderr = io.open("notebook.stderr.log", "wt")

    # Set dead man's switch
    def kill_me(num, stack):
        """Oblig. Alien reference."""
        sys.exit(66)

    signal.signal(signal.SIGALRM, kill_me)
    signal.alarm(kill_timeout)

    argv = ["notebook", "--debug"] + extra_argv

    assert port

    notebook_name = "default.ipynb"

    os.environ["IPYTHONDIR"] = os.path.join(os.getcwd(), ".ipython")

    # Update context file with command line port settings
    context = comm.get_context(pid_file)
    if not context:
        context = {}

    context["http_port"] = port
    context["pid"] = os.getpid()
    context["kill_timeout"] = kill_timeout
    comm.set_context(pid_file, context)

    create_named_notebook(notebook_name, context)

    def clear_context():
        comm.clear_context(pid_file)

    atexit.register(clear_context)

    # Grind through with print as IPython launcher would mess our loggers
    print("Launching on localhost:{}, having context {}".format(port, str(context)), file=sys.stderr)

    try:
        import IPython

        config = IPython.Config()

        config.NotebookApp.port = port
        config.NotebookApp.open_browser = foreground
        config.NotebookApp.base_url = context.get("notebook_path", "/notebook")
        config.NotebookApp.log_level = logging.DEBUG
        config.NotebookApp.allow_origin = context.get("allow_origin", "http://localhost:{}/".format(port))

        if "websocket_url" in context:
            websocket_url = context.get("websocket_url", "http://localhost:{}/".format(port))
            config.NotebookApp.websocket_url = websocket_url

        if "startup" in context:
            # Drop in custom startup script
            startup_folder = os.path.join(os.getcwd(), ".ipython/profile_default/startup/")
            os.makedirs(startup_folder, exist_ok=True)
            startup_py = os.path.join(startup_folder, "startup.py")
            print("Dropping startup script {}".format(startup_py), file=sys.stderr)
            with open(startup_py, "wt") as f:
                f.write(context["startup"])

        ipython = IPython.start_ipython(argv=argv, config=config)

    except Exception as e:
        import traceback ; traceback.print_exc()
        sys.exit(str(e))

if __name__ == '__main__':

    if len(sys.argv) == 1:
        sys.exit("Usage: {} start|stop|status|fg pid_file [work_folder] [notebook port] [kill timeout in seconds] *extra_args")

    action = sys.argv[1]
    pid_file = sys.argv[2]

    if action in ("start", "restart", "fg"):
        workdir = sys.argv[3]
        port = int(sys.argv[4])
        kill_timeout = int(sys.argv[5])
        extra_argv = sys.argv[6:]
    else:
        workdir = os.getcwd()

    os.makedirs(workdir, exist_ok=True)

    if action == "fg":
        # Test run on foreground
        os.chdir(workdir)
        run_notebook(foreground=True)
    else:
        daemon = NotebookDaemon(pidfile=pid_file, workdir=workdir)
        daemon.worker = run_notebook
        daemon.do_action(action)

    sys.exit(0)