"""

    Communicate with notebook daemon process with named file.

    When the notebook daemon is started, dump all special settings, including ports, in a named file similar to PID file.

    Note that port is delivered through command line AND context file. This is to allow starting daemon from the command line for testing without cumbersome writing of context file first.

    {
        "http_port",
        "pid",
        "allow_origin"

        # Overried websocket URL
        "websocket_url",

        # URL path where Notebook is proxyed
        "notebook_path",

        # Hashed information of the started notebook varibles.
        # If hash changes -> extra_context has changed and we need to restart.
        "extra_context_hash",
        "extra_context": {}
    }

"""
import json
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

    assert type(context_info) == dict

    port_file = get_context_file_name(pid_file)
    with open(port_file, "wt") as f:
        f.write(json.dumps(context_info))


def get_context(pid_file):
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

        pid = data.get("pid")
        if pid and not check_pid(int(pid)):
            # The Notebook daemon has exited uncleanly, as the PID does not point to any valid process
            return None


        return data


def clear_context(pid_file):
    """Called at exit. Delete the context file to signal there is no active notebook."""
    port_file = get_context_file_name(pid_file)
    os.remove(port_file)