import logging
from pyramid.config import Configurator
from pyramid.authentication import BasicAuthAuthenticationPolicy
from pyramid.interfaces import IDebugLogger

from . import views
from . import auth


def mycheck(username, password, request):
    """Allow in any user with password "password"""""
    pwd_ok = password == "password"
    if not pwd_ok:
        return None
    return ['authenticated']


def main(global_config, **settings):

    settings["global_config"] = global_config
    config = Configurator(settings=settings)

    # Jinja 2 templates as .html files
    config.include('pyramid_jinja2')
    config.add_jinja2_renderer('.html')
    config.add_jinja2_search_path('pyramid_notebook:demo/templates', name='.html')

    config.add_route('home', '/')
    config.add_route('login', '/login')
    config.add_route('shell1', '/shell1')
    config.add_route('shell2', '/shell2')
    config.add_route('shutdown_notebook', '/notebook/shutdown')
    config.add_route('notebook_proxy', '/notebook/*remainder')

    config.scan(views)

    authn_policy = auth.AuthTktAuthenticationPolicy('seekrITT', callback=auth.groupfinder)
    config.set_authentication_policy(BasicAuthAuthenticationPolicy(mycheck))
    config.set_authorization_policy(authn_policy)

    # Make sure we can target Pyramid router debug messages in logging configuration
    pyramid_debug_logger = logging.getLogger("pyramid_debug")
    config.registry.registerUtility(pyramid_debug_logger, IDebugLogger)

    return config.make_wsgi_app()


