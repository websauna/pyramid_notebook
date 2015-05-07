import json
import hashlib
import logging
from ssl import socket_error
import time
from socket import error as socket_error
import errno
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPInternalServerError

from pyramid.wsgi import wsgiapp

from pyramid_notebook.notebookmanager import NotebookManager
from pyramid_notebook.proxy import WSGIProxyApplication
from pyramid_notebook.utils import make_dict_hash


logger = logging.getLogger(__name__)



def proxy_it(request, port):
    proxy_app = WSGIProxyApplication(port)
    return request.get_response(proxy_app)


def security_check(request, username):
    """Check for basic misconfiguration errors."""
    assert username, "You must give an username whose IPython Notebook session we open"


def launch_on_demand(request, username, notebook_context):

    security_check(request, username)

    settings = request.registry.settings

    notebook_folder = settings.get("pyramid_notebook.notebook_folder", None)
    if not notebook_folder:
        raise RuntimeError("Setting missing: pyramid_notebook.notebook_folder")

    kill_timeout = settings.get("pyramid_notebook.kill_timeout", None)
    if not kill_timeout :
        raise RuntimeError("Setting missing: pyramid_notebook.kill_timeout")

    kill_timeout = int(kill_timeout)

    if not notebook_context:
        notebook_context = {}

    # Record the hash of the current parameteres, so we know if this user accesses the notebook in this or different context
    if not "context_hash" in notebook_context:
        notebook_context["context_hash"] = make_dict_hash(notebook_context)

    # Tell notebook to correctly address WebSockets allow origin policy
    notebook_context["allow_origin"] = request.host_url
    notebook_context["notebook_path"] = request.route_path("notebook_proxy", remainder="")

    manager = NotebookManager(notebook_folder, kill_timeout=kill_timeout)
    notebook_info, created  = manager.start_notebook_on_demand(username, notebook_context)
    return notebook_info


def notebook_proxy(request, username):
    """Renders a IPython Notebook frame wrapper.

    Starts or reattachs ot an existing Notebook session.
    """
    security_check(request, username)

    settings = request.registry.settings
    notebook_folder = settings["pyramid_notebook.notebook_folder"]
    manager = NotebookManager(notebook_folder)
    notebook_info = manager.get_context(username)

    if not notebook_info:
        raise HTTPInternalServerError("Apparently IPython Notebook daemon process is not running for {}".format(username))

    return proxy_it(request, notebook_info["http_port"])



def launch_notebook(request, username, notebook_context):
    """Renders a IPython Notebook frame wrapper.

    Starts or reattachs ot an existing Notebook session.
    """
    # The notebook manage now tries too hard to get the port allocated for the notebook user, making it slow
    # TODO: Manage a proper state e.g. using Redis
    notebook_info = launch_on_demand(request, username, notebook_context)

    # Jump to the detault notebook
    return HTTPFound(request.route_url("notebook_proxy", remainder="notebooks/default.ipynb"))
