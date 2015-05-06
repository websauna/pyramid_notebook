import json
import port_for
import logging
import subprocess
import os
import sys

logger = logging.getLogger(__name__)


class NotebookManager:
    """Manage any number of detached running Notebook instances.

    * Start instance by name, assign a port
    * Get instance by name
    * Stop instance by name
    * Pass extra parameters to IPython Nobetook
    """

    def __init__(self, notebook_folder, cmd="ipython", min_port=40000, port_range=10, kill_timeout=50, python=sys.executable):
        """
        :param notebook_folder: A folder containing a subfolder for each named IPython Notebook. The subfolder contains pid file, log file, default.ipynb and profile files.
        """
        self.min_port = min_port
        self.port_range = port_range
        self.notebook_folder = notebook_folder
        self.kill_timeout = kill_timeout
        self.python = python

        assert os.path.exists(notebook_folder), "Does not exist {}".format(notebook_folder)

        self.cmd = self.get_manager_cmd()

    def get_work_folder(self, name):
        work_folder = os.path.join(self.notebook_folder, name)
        os.makedirs(work_folder, exist_ok=True)
        return work_folder

    def get_pid(self, name):
        """Get PID file name for a named notebook."""
        pid_file = os.path.join(self.get_work_folder(name), "notebook.pid")
        return pid_file

    def get_manager_cmd(self):
        """Get our daemon script path."""
        cmd = os.path.abspath(os.path.join(os.path.dirname(__file__), "server", "notebook_daemon.py"))
        assert os.path.exists(cmd)
        return cmd

    def pick_port(self):
        """Pick open TCP/IP port."""
        ports = set(range(self.min_port, self.min_port + self.port_range))
        return port_for.select_random(ports)

    def get_notebook_daemon_command(self, name, action, http_port=0, *extra):
        """
        Assume we launch Notebook with the same Python which executed us.
        """

        if action in ("start", "fg", "restart"):
            http_port = self.pick_port()

        return [self.python, self.cmd, action, self.get_pid(name), self.notebook_folder, http_port, self.kill_timeout] + list(extra)

    def exec_notebook_daemon_command(self, name, cmd):
        """Run a daemon script command."""
        cmd = self.get_notebook_daemon_command(name, cmd)

        # Make all arguments explicit strings
        cmd = [str(arg) for arg in cmd]

        p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()

        if p.returncode != 0:
            logger.error("STDOUT: %s", stdout)
            logger.error("STDERR: %s", stderr)

            raise RuntimeError("Could not execute notebook command. Exit code: {} cmd: {}".format(p.returncode, cmd))

        return stdout

    def get_notebook_status(self, name):
        bytebytebyte = self.exec_notebook_daemon_command(name, "status")
        json_data = bytebytebyte.decode("utf-8")
        data = json.loads(json_data)
        return data

    def start_notebook(self, name):
        return self.exec_notebook_daemon_command(name, "start")

    def stop_notebook(self, name):
        return self.exec_notebook_daemon_command(name, "stop")




