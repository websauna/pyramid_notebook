from pyramid import httpexceptions
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.security import forget
from pyramid.view import view_config, forbidden_view_config
from pyramid.httpexceptions import HTTPUnauthorized, HTTPFound


from pyramid_notebook.views import launch_notebook
from pyramid_notebook.views import shutdown_notebook as _shutdown_notebook
from pyramid_notebook.views import notebook_proxy as _notebook_proxy
from pyramid_notebook import startup


SCRIPT = """
a = "foo"
b = "bar"

def fn():
    print("buu")
"""

GREETING="""
* **a** - varible a
* **b** - variable b
* **fn** - test function
"""


@view_config(route_name="home", renderer="templates/home.html")
def home(request):
    return {}


@view_config(route_name="notebook_proxy", renderer="templates/login.html")
def notebook_proxy(request):

    # Make sure we have a logged in user
    auth = request.registry.queryUtility(IAuthenticationPolicy)
    username = auth.authenticated_userid(request)

    if not username:
        # This will trigger HTTP Basic Auth dialog, as per basic_challenge handler below
        raise httpexceptions.HTTPForbidden("You need to be logged in. Hint: user / password")


    return _notebook_proxy(request, username)


@view_config(route_name="shell1")
def shell1(request):

    # Make sure we have a logged in user
    auth = request.registry.queryUtility(IAuthenticationPolicy)
    username = auth.authenticated_userid(request)

    if not username:
        # This will trigger HTTP Basic Auth dialog, as per basic_challenge handler below
        raise httpexceptions.HTTPForbidden("You need to be logged in. Hint: user / password")

    notebook_context = {"greeting": "**Executing shell1 context**\n"}
    config_file = request.registry.settings["global_config"]["__file__"]
    startup.make_startup(notebook_context, config_file)

    return launch_notebook(request, username, notebook_context=notebook_context)


@view_config(route_name="shell2")
def shell2(request):

    # Make sure we have a logged in user
    auth = request.registry.queryUtility(IAuthenticationPolicy)
    username = auth.authenticated_userid(request)

    if not username:
        # This will trigger HTTP Basic Auth dialog, as per basic_challenge handler below
        raise httpexceptions.HTTPForbidden("You need to be logged in. Hint: user / password")

    notebook_context = {"greeting": "**Executing shell2 context**\n"}
    config_file = request.registry.settings["global_config"]["__file__"]
    startup.make_startup(notebook_context, config_file)
    startup.add_script(notebook_context, SCRIPT)
    startup.add_greeting(notebook_context, GREETING)

    return launch_notebook(request, username, notebook_context=notebook_context)


@view_config(route_name="shutdown_notebook")
def shutdown_notebook(request):

    # Make sure we have a logged in user
    auth = request.registry.queryUtility(IAuthenticationPolicy)
    username = auth.authenticated_userid(request)

    if not username:
        # This will trigger HTTP Basic Auth dialog, as per basic_challenge handler below
        raise httpexceptions.HTTPForbidden("You need to be logged in. Hint: user / password")

    _shutdown_notebook(request, username)

    return HTTPFound(request.route_url("home"))


@forbidden_view_config()
def basic_challenge(request):
    response = HTTPUnauthorized()
    response.headers.update(forget(request))
    return response