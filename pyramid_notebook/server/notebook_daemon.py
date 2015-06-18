"""Daemonized Python Notebook process with pre-allocated port, kill timeout and extra argument passing through JSON file."""
from contextlib import redirect_stdout
import logging

import json
import time
from IPython.nbformat.v4.nbjson import JSONWriter
import io
import os
import atexit
import signal
import sys
import faulthandler

import daemonocle
from daemonocle import expose_action
from daemonocle import DaemonError
import psutil
from pyramid_notebook.server import comm

try:
    import coverage
    coverage.process_startup()
except ImportError:
    # http://nedbatchelder.com/code/coverage/subprocess.html
    pass

port = None
kill_timeout = None
extra_argv = None
pid_file = None


class NotebookDaemon(daemonocle.Daemon):

    def __init__(self, **kwargs):
        super(NotebookDaemon, self).__init__(**kwargs)

    @expose_action
    def stop(self):
        """Stop the daemon.

        IPython Notebook tends to hang on exit 1) on certain Linux servers 2) sometimes.
        I am not sure why, but here is the traceback back when gdb was attached to the process::

            #0  0x00007fa7632c912d in poll () at ../sysdeps/unix/syscall-template.S:81
            #1  0x00007fa75e6d2f6a in poll (__timeout=<optimized out>, __nfds=2, __fds=0x7fffd2c60940) at /usr/include/x86_64-linux-gnu/bits/poll2.h:46
            #2  zmq_poll (items_=items_@entry=0x2576f00, nitems_=nitems_@entry=2, timeout_=timeout_@entry=2997) at bundled/zeromq/src/zmq.cpp:736
            #3  0x00007fa75d0d7c0b in __pyx_pf_3zmq_7backend_6cython_5_poll_zmq_poll (__pyx_self=<optimized out>, __pyx_v_timeout=2997, __pyx_v_sockets=0x7fa75b82c848) at zmq/backend/cython/_poll.c:1552
            #4  __pyx_pw_3zmq_7backend_6cython_5_poll_1zmq_poll (__pyx_self=<optimized out>, __pyx_args=<optimized out>, __pyx_kwds=<optimized out>) at zmq/backend/cython/_poll.c:1023
            #5  0x000000000057bf33 in PyEval_EvalFrameEx ()
            #6  0x000000000057d3d3 in PyEval_EvalCodeEx ()

        Smells like pyzmq bug. In any it would take pretty extensive debugging to find out why it doesn't always quit cleanly, so we just SIGKILL the process after certain timeout.

        Related bug, but this should be apparently fixed: https://github.com/zeromq/pyzmq/pull/618
        """
        if self.pidfile is None:
            raise DaemonError('Cannot stop daemon without PID file')

        pid = self._read_pidfile()
        if pid is None:
            # I don't think this should be a fatal error
            self._emit_warning('{prog} is not running'.format(prog=self.prog))
            return

        self._emit_message('Stopping {prog} ... '.format(prog=self.prog))

        try:
            # Try to terminate the process
            os.kill(pid, signal.SIGTERM)
        except OSError as ex:
            self._emit_failed()
            self._emit_error(str(ex))
            sys.exit(1)

        _, alive = psutil.wait_procs([psutil.Process(pid)], timeout=self.stop_timeout)
        if alive:
            # The process didn't terminate for some reason
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.5)
            # Hahahaha. Do you feel alive now?

        self._emit_ok()

def create_named_notebook(fname, context):
    """Create a named notebook if one doesn't exist."""

    if os.path.exists(fname):
        return

    from IPython.nbformat import v4 as nbf

    # Courtesy of http://nbviewer.ipython.org/gist/fperez/9716279
    text = "Welcome to *pyramid_notebook!* -Mikko, https://opensourcehacker.com"
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

    if not foreground:
        # Make it possible to get output what daemonized IPython is doing
        sys.stdout = io.open("notebook.stdout.log", "wt")
        sys.stderr = io.open("notebook.stderr.log", "wt")

    try:
        _run_notebook(foreground)
    except:
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise


def _run_notebook(foreground=False):

    print("Starting notebook, daemon {}".format(not foreground), file=sys.stderr)

    # Set dead man's switch
    def kill_me(num, stack):
        """Oblig. Alien reference."""
        sys.exit(66)

    signal.signal(signal.SIGALRM, kill_me)
    signal.alarm(kill_timeout)

    argv = ["notebook", "--debug"] + extra_argv

    assert port

    os.environ["IPYTHONDIR"] = os.path.join(os.getcwd(), ".ipython")

    # Update context file with command line port settings
    context = comm.get_context(pid_file, daemon=True)

    if foreground:
        if not context:
            context = {}
    else:
        if not context:
            # We cannot let daemons start up with context, because it keeps running, reverses port but would do all proxy setup wrong
            sys.exit("Daemonized process needs an explicit context.json file and could not read one from {}".format(os.path.dirname(pid_file)))

        if "terminated" in context:
            print("Invalid context file {}: {}".format(os.path.dirname(pid_file), context), file=sys.stderr)
            sys.exit("Bad context - was by terminated notebook daemon")

        print("Starting with context {}".format(context), file=sys.stderr)

    hash = context["context_hash"]
    if hash < 0:
        # Python hasher can create negative integers which look funny in URL.
        # Let's sacrifice one bit of hash collision for aesthetics.
        hash = -hash

    notebook_name = "default-{}.ipynb".format(hash)

    context["http_port"] = port
    context["pid"] = os.getpid()
    context["kill_timeout"] = kill_timeout
    context["notebook_name"] = notebook_name

    comm.set_context(pid_file, context)

    create_named_notebook(notebook_name, context)

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
        config.NotebookApp.extra_template_paths = context.get("extra_template_paths", [])

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


def clear_context(*args):
    comm.clear_context(pid_file)


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
        atexit.register(clear_context)
        run_notebook(foreground=True)
    else:

        def shutdown(message, code):
            f = io.open("/tmp/notebook.shutdown.dump", "wt")
            faulthandler.dump_traceback(f)
            print("shutdown {}: {}".format(message, code), file=sys.stderr)
            sys.stderr.flush()
            clear_context()

        f = io.open("/tmp/notebook.dump", "wt")
        faulthandler.enable(f)

        daemon = NotebookDaemon(pidfile=pid_file, workdir=workdir, shutdown_callback=shutdown)
        daemon.worker = run_notebook
        daemon.do_action(action)
