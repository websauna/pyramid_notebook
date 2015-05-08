"""Communicate extra parameters to the notebook through a JSON file.

    When the notebook daemon is started, dump all special settings, including ports, in a named file similar to PID file.

    Note that port is delivered through command line AND context file. This is to allow starting daemon from the command line for testing without cumbersome writing of context file first.


"""
import datetime
import json
import shutil
import os
import logging


logger = logging.getLogger(__name__)


# http://stackoverflow.com/a/568285/315168
def check_pid(pid):
    """ Check For the existence of a unix pid. """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def get_context_file_name(pid_file):
    """When the daemon is started write out the information which port it was using."""
    root = os.path.dirname(pid_file)
    port_file = os.path.join(root, "context.json")
    return port_file


def set_context(pid_file, context_info):
    """Set context of running notebook.

    :param context_info: dict of extra context parameters, see comm.py comments
    """
    assert type(context_info) == dict

    port_file = get_context_file_name(pid_file)
    with open(port_file, "wt") as f:
        f.write(json.dumps(context_info))


def get_context(pid_file, daemon=False):
    """Get context of running notebook.

    :param daemon: Are we trying to fetch the context inside the daemon. Otherwise do the death check.

    :return: dict or None if the process is dead/not launcherd
    """
    port_file = get_context_file_name(pid_file)

    if not os.path.exists(port_file):
        return None

    with open(port_file, "rt") as f:
        json_data = f.read()
        try:
            data = json.loads(json_data)
        except ValueError as e:

            logger.error("Damaged context json data %s", json_data)
            return None

        if not daemon:
            pid = data.get("pid")
            if pid and not check_pid(int(pid)):
                # The Notebook daemon has exited uncleanly, as the PID does not point to any valid process
                return None


        return data


def clear_context(pid_file):
    """Called at exit. Delete the context file to signal there is no active notebook.

    We don't delete the whole file, but leave it around for debugging purposes. Maybe later we want to pass some information back to the web site.
    """
    return
    raise RuntimeError("Should not happen")
    fname = get_context_file_name(pid_file)
    shutil.move(fname, fname.replace("context.json", "context.old.json"))

    data = {}
    data["terminated"] = str(datetime.datetime.now(datetime.timezone.utc))
    set_context(pid_file, data)


