"""Functional testing with WSGI server."""


import threading
import time
from wsgiref.simple_server import make_server
from urllib.parse import urlparse
import os

from pyramid.paster import get_appsettings
from pyramid.paster import setup_logging


import pytest
from webtest import TestApp



def pytest_addoption(parser):
    parser.addoption("--ini", action="store", metavar="INI_FILE", help="use INI_FILE to configure SQLAlchemy")


@pytest.fixture(scope='session')
def ini_settings(request):
    """Load INI settings from py.test command line."""
    if not getattr(request.config.option, "ini", None):
        raise RuntimeError("You need to give --ini test.ini command line option to py.test to find our test settings")

    config_uri = os.path.abspath(request.config.option.ini)
    setup_logging(config_uri)
    config = get_appsettings(config_uri)

    return config_uri, config



class ServerThread(threading.Thread):
    """ Run WSGI server on a background thread.

    Pass in WSGI app object and serve pages from it for Selenium browser.
    """

    def __init__(self, app, hostbase):
        threading.Thread.__init__(self)
        self.app = app
        self.srv = None
        self.daemon = True
        self.hostbase = hostbase

    def run(self):
        """
        Open WSGI server to listen to HOST_BASE address
        """
        print("Running")
        parts = urlparse(self.hostbase)
        domain, port = parts.netloc.split(":")
        print(domain, port)
        self.srv = make_server(domain, int(port), self.app)
        try:
            self.srv.serve_forever()
        except:
            # We are a background thread so we have problems to interrupt tests in the case of error
            import traceback
            traceback.print_exc()
            # Failed to start
            self.srv = None

    def quit(self):
        """Stop test webserver."""
        print("Shutdown")
        if self.srv:
            self.srv.shutdown()



@pytest.fixture(scope='session')
def web_server(request, ini_settings):
    """Creates a test web server which does not give any CSS and JS assets to load.

    Because the server life-cycle is one test session and we run with different settings we need to run a in different port.
    """

    from pyramid_notebook import demo

    config_uri, settings = ini_settings
    app = demo.main({"__file__": config_uri}, **settings)

    port = 8777

    host_base = "http://localhost:{}".format(port)
    server = ServerThread(app, host_base)
    server.start()

    # Wait randomish time to allows SocketServer to initialize itself.
    # TODO: Replace this with proper event telling the server is up.
    time.sleep(0.1)

    assert server.srv is not None, "Could not start the test web server"

    app = TestApp(app)

    def teardown():
        server.quit()

    request.addfinalizer(teardown)

    return {"host_base": host_base, "port": port}

