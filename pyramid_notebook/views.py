import logging
import os
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPInternalServerError

from pyramid_notebook.notebookmanager import NotebookManager
from pyramid_notebook.proxy import WSGIProxyApplication
from pyramid_notebook.utils import make_dict_hash


logger = logging.getLogger(__name__)



def proxy_it(request, port):
    """Proxy HTTP request to upstream IPython Notebook Tornado server."""

    if request.method == "POST" and not request.headers.get("Content-length"):
        # It is possible to get a POST request with content-length set by the browser. This happens with X-Requested-With:XMLHttpRequest when IPython Notebook does session POST call. The magic below forces us the read the whole request and makes the Content-length magically to appear for the upstream proxy which otherwise would get 400 Bad Request from Tornado. Furthermore to add to the insult this happened on the same computer on two different Pyramid installations which should have the same pindowns, so not sure what is triggering the actual problem.
        # request.body  # touch body, make it to read it fully?
        # assert request.headers.get("Content-length")
        pass

    proxy_app = WSGIProxyApplication(port)
    return request.get_response(proxy_app)


def security_check(request, username):
    """Check for basic misconfiguration errors."""
    assert username, "You must give an username whose IPython Notebook session we open"


def prepare_notebook_context(request, notebook_context):
    """Fill in notebook context with default values."""

    if not notebook_context:
        notebook_context = {}

    # Override notebook Jinja templates
    if "extra_template_paths" not in notebook_context:
        notebook_context["extra_template_paths"] = [os.path.join(os.path.dirname(__file__), "server", "templates")]

    # Furious invalid state follows if we let this slip through
    assert type(notebook_context["extra_template_paths"]) == list, "Got bad extra_template_paths {}".format(notebook_context["extra_template_paths"])

    # Jinja variables
    notebook_context["jinja_environment_options"] = notebook_context.get("jinja_environment_options", {})

    assert type(notebook_context["jinja_environment_options"]) == dict

    # XXX: Following passing of global variables to Jinja templates requires Jinja 2.8.0dev+ version and is not yet supported
    # http://jinja.pocoo.org/docs/dev/api/#jinja2.Environment.globals

    # notebook_context["jinja_environment_options"]["globals"] = notebook_context["jinja_environment_options"].get("globals", {})
    # globals_ = notebook_context["jinja_environment_options"]["globals"]
    #
    # assert type(globals_) == dict
    #
    # if not "home_url" in globals_:
    #     globals_["home_url"] = request.host_url
    #
    # if not "home_title" in globals_:
    #     globals_["home_title"] = "Back to site"

    # Tell notebook to correctly address WebSockets allow origin policy
    notebook_context["allow_origin"] = request.host_url
    notebook_context["notebook_path"] = request.route_path("notebook_proxy", remainder="")

    # Record the hash of the current parameters, so we know if this user accesses the notebook in this or different context
    if "context_hash" not in notebook_context:
        notebook_context["context_hash"] = make_dict_hash(notebook_context)


    print(notebook_context)


def launch_on_demand(request, username, notebook_context):
    """See if we have notebook already running this context and if not then launch new one."""
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

    # Override notebook Jinja templates
    if "extra_template_paths" not in notebook_context:
        notebook_context["extra_template_paths"] = [os.path.join(os.path.dirname(__file__), "server", "templates")]

    # Furious invalid state follows if we let this slip through
    assert type(notebook_context["extra_template_paths"]) == list, "Got bad extra_template_paths {}".format(notebook_context["extra_template_paths"])
    notebook_folder = settings.get("pyramid_notebook.notebook_folder", None)
    if not notebook_folder:
        raise RuntimeError("Setting missing: pyramid_notebook.notebook_folder")

    kill_timeout = settings.get("pyramid_notebook.kill_timeout", None)
    if not kill_timeout :
        raise RuntimeError("Setting missing: pyramid_notebook.kill_timeout")

    kill_timeout = int(kill_timeout)

    prepare_notebook_context(request, notebook_context)

    # Record the hash of the current parameters, so we know if this user accesses the notebook in this or different context
    if "context_hash" not in notebook_context:
        notebook_context["context_hash"] = make_dict_hash(notebook_context)


    manager = NotebookManager(notebook_folder, kill_timeout=kill_timeout)
    notebook_info, created = manager.start_notebook_on_demand(username, notebook_context)
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

    if not "http_port" in notebook_info:
        raise RuntimeError("Notebook terminated prematurely before managed to tell us its HTTP port")

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


def shutdown_notebook(request, username):
    """Stop any running notebook for a user."""

    settings = request.registry.settings
    notebook_folder = settings["pyramid_notebook.notebook_folder"]
    manager = NotebookManager(notebook_folder)
    if manager.is_running(username):
        manager.stop_notebook(username)
