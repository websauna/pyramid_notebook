import json
import port_for
import logging
import subprocess
import os
import sys
import time

from .server import comm

logger = logging.getLogger(__name__)


class NotebookManager:
    """Manage any number of detached running Notebook instances.

    * Start instance by name, assign a port
    * Get instance by name
    * Stop instance by name
    * Pass extra parameters to IPython Nobetook
    """

    def __init__(self, notebook_folder, min_port=40000, port_range=10, kill_timeout=50, python=None):
        """
        :param notebook_folder: A folder containing a subfolder for each named IPython Notebook. The subfolder contains pid file, log file, default.ipynb and profile files.
        """
        self.min_port = min_port
        self.port_range = port_range
        self.notebook_folder = notebook_folder
        self.kill_timeout = kill_timeout

        if python:
            self.python = python
        else:
            self.python = self.discover_python()

        os.makedirs(notebook_folder, exist_ok=True)

        self.cmd = self.get_manager_cmd()

    def discover_python(self):
        """Get the Python interpreter we need to use to run our Notebook daemon."""
        python = sys.executable

        #: XXX fix this hack, uwsgi sets itself as Python
        #: Make better used Python interpreter autodiscovery
        if python.endswith("/uwsgi"):
            python = python.replace("/uwsgi", "/python")
        return python

    def get_work_folder(self, name):
        work_folder = os.path.join(self.notebook_folder, name)
        os.makedirs(work_folder, exist_ok=True)
        return work_folder

    def get_log_file(self, name):
        log_file = os.path.join(self.get_work_folder(name), "ipython.log")
        return log_file

    def get_pid(self, name):
        """Get PID file name for a named notebook."""
        pid_file = os.path.join(self.get_work_folder(name), "notebook.pid")
        return pid_file

    def get_context(self, name):
        return comm.get_context(self.get_pid(name))

    def get_manager_cmd(self):
        """Get our daemon script path."""
        cmd = os.path.abspath(os.path.join(os.path.dirname(__file__), "server", "notebook_daemon.py"))
        assert os.path.exists(cmd)
        return cmd

    def pick_port(self):
        """Pick open TCP/IP port."""
        ports = set(range(self.min_port, self.min_port + self.port_range))
        return port_for.select_random(ports)

    def get_notebook_daemon_command(self, name, action, port=0, *extra):
        """
        Assume we launch Notebook with the same Python which executed us.
        """

        return [self.python, self.cmd, action, self.get_pid(name), self.get_work_folder(name), port, self.kill_timeout] + list(extra)

    def exec_notebook_daemon_command(self, name, cmd, port=0):
        """Run a daemon script command."""
        cmd = self.get_notebook_daemon_command(name, cmd, port)

        # Make all arguments explicit strings
        cmd = [str(arg) for arg in cmd]

        logger.info("Running notebook command: %s", " ".join(cmd))

        # Add support for traceback dump on stuck
        env = os.environ.copy()
        env["PYTHONFAULTHANDLER"] = "true"

        p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, env=env)
        stdout, stderr = p.communicate()

        if p.returncode != 0:
            logger.error("STDOUT: %s", stdout)
            logger.error("STDERR: %s", stderr)

            raise RuntimeError("Could not execute notebook command. Exit code: {} cmd: {}".format(p.returncode, " ".join(cmd)))

        return stdout

    def get_notebook_status(self, name):
        """Get the running named Notebook status.

        :return: None if no notebook is running, otherwise context dictionary
        """
        context = comm.get_context(self.get_pid(name))
        if not context:
            return None
        return context

    def start_notebook(self, name, context:dict, fg=False):
        """Start new IPython Notebook daemon.

        :param name: The owner of the Notebook will be *name*. He/she gets a new Notebook content folder created where all files are placed.

        :param context: Extra context information passed to the started Notebook. This must contain {context_hash:int} parameter used to identify the launch parameters for the notebook
        """
        assert context
        assert type(context) == dict
        assert "context_hash" in context
        assert type(context["context_hash"]) == int

        http_port = self.pick_port()
        assert http_port
        context = context.copy()
        context["http_port"] = http_port

        # We can't proxy websocket URLs, so let them go directly through localhost or have front end server to do proxying (nginx)
        if not "websocket_url" in context:
            context["websocket_url"] = "ws://localhost:{port}".format(port=http_port)

        if "{port}" in context["websocket_url"]:
            # Do port substituion for the websocket URL
             context["websocket_url"] =  context["websocket_url"].format(port=http_port)

        pid = self.get_pid(name)
        assert not "terminated" in context

        comm.set_context(pid, context)

        if fg:
            self.exec_notebook_daemon_command(name, "fg", port=http_port)
        else:
            self.exec_notebook_daemon_command(name, "start", port=http_port)

    def stop_notebook(self, name):
        self.exec_notebook_daemon_command(name, "stop")

    def is_running(self, name):
        status = self.get_notebook_status(name)
        if status:
            return status.get("pid") is not None
        return False

    def is_same_context(self, context_a, context_b):
        if context_a == context_b:
            return True

        context_a = context_a or {}
        context_b = context_b or {}

        return context_a.get("context_hash") == context_b.get("context_hash")


    def start_notebook_on_demand(self, name, context):
        """Start notebook if not yet running with these settings.

        Return the updated settings with a port info.

        :return: (context dict, created flag)
        """
        if self.is_running(name):

            last_context = self.get_context(name)
            logger.info("Notebook context change detected for {}".format(name))
            if not self.is_same_context(context, last_context):
                self.stop_notebook(name)
                # Make sure we don't get race condition over context.json file
                time.sleep(2.0)
            else:
                return last_context, False

        logger.info("Launching new Notebook named %s, context is %s", name, context)
        logger.info("Notebook log is %s/notebook.stderr.log", self.get_work_folder(name))
        self.start_notebook(name, context)
        time.sleep(1)
        return self.get_context(name), True





