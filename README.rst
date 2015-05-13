Embed IPython Notebook shell on your Pyramid web site and start through-the-browser Python shell with a single click.

`IPython Notebook <http://ipython.org/notebook.html>`_ is the de facto tool for researches, data analysts and software developers to perform visual and batch oriented tasks. *pyramid_notebook* puts the power of IPython Notebook inside of a `Pyramid website <http://www.pylonsproject.org/projects/pyramid/about>`_.

.. |docs| image:: https://readthedocs.org/projects/cryptoassetscore/badge/?version=latest
    :target: http://cryptoassetscore.readthedocs.org/en/latest/

.. |ci| image:: https://drone.io/bitbucket.org/miohtama/pyramid_notebook/status.png
    :target: https://drone.io/bitbucket.org/miohtama/pyramid_notebook/latest

.. |cov| image:: https://codecov.io/bitbucket/miohtama/pyramid_notebook/coverage.svg?branch=master
    :target: https://codecov.io/bitbucket/miohtama/pyramid_notebook?branch=master

.. |downloads| image:: https://pypip.in/download/pyramid_notebook/badge.png
    :target: https://pypi.python.org/pypi/pyramid_notebook/
    :alt: Downloads

.. |latest| image:: https://pypip.in/version/pyramid_notebook/badge.png
    :target: https://pypi.python.org/pypi/pyramid_notebook/
    :alt: Latest Version

.. |license| image:: https://pypip.in/license/pyramid_notebook/badge.png
    :target: https://pypi.python.org/pypi/pyramid_notebook/
    :alt: License

.. |versions| image:: https://pypip.in/py_versions/pyramid_notebook/badge.png
    :target: https://pypi.python.org/pypi/pyramid_notebook/
    :alt: Supported Python versions

+-----------+-----------+
| |cov|     ||downloads||
+-----------+-----------+
| |ci|      | |license| |
+-----------+-----------+
| |versions|| |latest|  |
+-----------+-----------+

.. contents:: :local:

Benefits
=========

* Easy access: All through web browser, no additional software installation needed.

* Automatic data sources: Populate Notebook with variables and data depending where the user clicks the shell open.

* Authentication integration: use the same credentials as you use for the site administration. Each Pyramid user gets his/her own IPython Notebook process.

Use cases
---------

* Visualize and analyze your website data.

* Easier and powerful alternative for normal Python prompt - web browser user interface has more candy over old fashioned terminal.

* Share code sessions and recipes with your team mates.

Prerequisites
-------------

* `Pyramid web site <http://www.pylonsproject.org/projects/pyramid/about>`_ (can be easily extended to other web frameworks)

* Python 3.3+

* OSX, Linux

* uWSGI (on production server only)

Demo
====

* Checkout source code repository::

    git clone https://miohtama@bitbucket.org/miohtama/pyramid_notebook.git

* Create virtualenv for Python 3.4. Install dependencies::

    cd pyramid_notebook
    virtualenv --python=python3.4 venv
    source venv/bin/activate
    pip install requirements.txt
    python setup.py develop

* Run demo::

    pserve pyramid_notebook/demo/development.ini

Then point your browser at `http://localhost:9999 <http://localhost:9999>`_.

Try accounts is *user* / *password*, and *user2* / *password* respectively.

Installation
============

It is recommend to install using ``pip`` and ``virtualenv``. `Python guide for package installation <https://packaging.python.org/en/latest/installing.html>`_. ::

    pip install pyramid_notebook

On production server where you use uWSGI websocket support::

    pip install pyramid_notebook[uwsgi]

Usage
=====

Your application needs to configure three custom views.

* One or multiple ``launch_ipython()`` notebook launch points. This does user authentication and authorization and then calls ``pyramid_notebook.views.launch_notebook()`` to open a new Notebook for a user. ``launch_ipython()`` takes in Notebook context parameters (see below), starts a new Notebook kernel if needed and then redirects user to Notebook itself.

* ``shutdown_ipython()`` which does authentication and authorization and calls ``pyramid_notebook.views.shutdown_notebook()`` to force close a notebook for a user.

* ``notebook_proxy()`` which does authentication and authorization and calls ``pyramid_notebook.views.notebook_proxy()`` to proxy HTTP request to upstream IPython Notebook server bind to a localhost port. `notebook_proxy` is mapped to `/notebook/` path in your site URL. Both your site and Notebook upstream server should agree on this location.

Example code
------------

The following is an example how to construct ``admin_shell`` view which launches a Notebook for the currently logged in Pyramid user when the view is visited for the first time. For extra security the permission for the notebook view cannot be assigned through normal groups, but the username must be on the whitelist in the INI settings file. This guarantees the shell is initially accessible only by persons who have shell access to the server itself.

For another approach on these views, please see the demo source code.

``views.py``:

.. code-block:: python

    from pyramid.httpexceptions import HTTPFound
    from pyramid.view import view_config
    from pyramid_notebook import startup
    from pyramid_notebook.views import launch_notebook
    from pyramid_notebook.views import shutdown_notebook as _shutdown_notebook
    from pyramid_notebook.views import notebook_proxy as _notebook_proxy
    from pyramid_web20.models import Base


    #: Include our database session in notebook so it is easy to query stuff right away from the prompt
    SCRIPT = """
    from pyramid_web20.models import DBSession as session
    """


    GREETING="""
    * **session** - SQLAlchemy database session
    """


    @view_config(route_name="notebook_proxy", permission="shell")
    def notebook_proxy(request):
        """Proxy IPython Notebook requests to the upstream server."""
        return _notebook_proxy(request, request.user.username)


    @view_config(route_name="admin_shell", permission="shell")
    def admin_shell(request):
        """Open admin shell with default parameters for the user."""
        # Make sure we have a logged in user
        nb = {}

        # Pass around the Pyramid configuration we used to start this application
        global_config = request.registry.settings["pyramid_web20.global_config"]

        # Get the reference to our Pyramid app config file and generate Notebook
        # bootstrap startup.py script for this application
        config_file = global_config["__file__"]
        startup.make_startup(nb, config_file)
        startup.add_script(nb, SCRIPT)
        startup.add_greeting(nb, GREETING)

        #: Include all our SQLAlchemy models in the notebook variables
        startup.include_sqlalchemy_models(nb, Base)

        return launch_notebook(request, request.user.username, notebook_context=nb)


    @view_config(route_name="shutdown_notebook", permission="shell")
    def shutdown_notebook(request):
        """Shutdown the notebook of the current user."""
        _shutdown_notebook(request, request.user.username)
        return HTTPFound(request.route_url("home"))

We also need to capture the INI settings file on the server start up, so that we can pass it forward to IPython Notebook process. In ``__init__.py``:

.. code-block:: python

    def main(global_config, **settings):
        settings["pyramid_web20.global_config"] = global_config

Then we have a custom principals handler granting the ``shell`` permission for users read from the user whitelist in the configuration file:

.. code-block:: python

    def find_groups(userid, request):
        """Get applied groups and other for the user"""

        from horus.interfaces import IUserClass
        user_class = request.registry.queryUtility(IUserClass)

        # Read superuser names from the config
        superusers = aslist(request.registry.settings.get("pyramid_web20.superusers"))

        user = models.DBSession.query(user_class).get(userid)
        if user:
            if user.can_login():
                principals = ['group:{}'.format(g.name) for g in user.groups]

            # Allow superuser permission
            if user.username in superusers or user.email in superusers:
                principals.append("superuser:superuser")

            return principals

        # User not found, user disabled
        return None

We refer to ``superuser:super`` in Pyramid site root object::

    class Root:

        __acl__ = [
            ...
            (Allow, "superuser:superuser", 'shell'),
        ]

And here is the configuration file bit::

    pyramid_web20.superusers =
        mikko@example.com

Pyramid settings
----------------

*python_notebook* reads following parameters from your Pyramid INI configuration file::

    # Where we store IPython Notebook runtime and persistent files
    # (pid, saved notebooks, etc.).
    # Each user will get a personal subfolder in this folder
    pyramid_notebook.notebook_folder = /tmp/pyramid_notebook

    # Automatically shutdown IPython Notebook kernel
    # after his many seconds have elapsed since startup
    pyramid_notebook.kill_timeout = 3600

    # Websocket proxy launch function.
    # This is a view function that upgrades the current HTTP request to Websocket (101 upgrade protocol)
    # and starts the web server websocket proxy loop. Currently only uWSGI supported
    # (see below).
    pyramid_notebook.websocket_proxy =

    # For uWSGI in production
    # pyramid_notebook.websocket_proxy = pyramid_notebook.uwsgi.serve_websocket

Notebook context parameters
---------------------------

Notebooks can be opened with context sensitive parameters. Some are filled in by the framework, some of those you can set yourself.

* You pass in your Notebook context parameters when you call ``launch_notebook()``.

* To have custom context variables change *startup* script.

* To have different info screen change *greeting* text

Example of what context information you can pass below::

    {

        # Extra Python script executed on notebook startup - this is saved as startup.py
        "startup": ""

        # Markdown text displayed at the beginning of the notebook
        "greeting": ""

        # List of paths where to load IPython Notebook Jinja templates
        # http://ipython.org/ipython-doc/3/config/options/notebook.html
        "extra_template_paths": []

        # The port where Notebook daemon is supposed to start listening to
        "http_port",

        # Notebook daemon process id - filled it in by the daemon itself
        "pid",

        # Notebook daemon kill timeout in seconds - filled in by the the daemon itself after parsing command line arguments
        "kill_timeout",

        # Bound localhost port for this notebook - filled in by the daemon itself after parsing command line arguments
        "http_port",

        # Set Notebook HTTP Allow Origin header to tell where websockets are allowed to connect
        "allow_origin"

        # Override websocket URL
        "websocket_url",

        # Path in URL where Notebook is proxyed, must match notebook_proxy() view
        "notebook_path",

        # Hash of this context. This is generated automatically from supplied context dictionary if not given. If the hash changes the notebook is restarted with new context data.
        "context_hash",
    }


Dead man switch
---------------

Launched Notebook processes have maximum life time after which they terminate themselves. Currently the termation is unconditional seconds since the start up, but in the future versions this is expected to change to a dead man switchs where the process only terminates itself if there has not been recent activity.

Websocket proxying
------------------

IPython Notebook needs two different kind of connections to function properly

* HTTP connection for loading the pages, assets

* Websocket for real-time communication with Notebook kernel

When you run Pyramid's ``pserve`` development server on your local machine and enter the Notebook shell, the websocket connection is made directly to IPython Notebook port bound localhost. This is because ``pserve`` does not have any kind of support for websockets. This behavior is controlled by ``pyramid_notebook.websocket_proxy`` setting.

On the production server, you usually run a web server which spawns processes to execute WSGI requests, the Python standard for hosting web applications. Unfortunately, like WSGI for HTTP, there doesn't exist a standard for doing websocket requests in a Python application. Thus, one has to add support for websockets for each web server separately. Currently *pyramid_notebook* supports the following web servers

 * `uWSGI <https://uwsgi-docs.readthedocs.org/en/latest/>`_

It is ok to have another web server at the front of uWSGI, like Nginx, as these web servers can usually do proxy pass for websocket connections.

uWSGI
~~~~~

To turn on websocket support on your uWSGI production server add following to your production INI settings::

    pyramid_notebook.websocket_proxy = pyramid_notebook.uwsgi.serve_websocket

Also you need to enable websockets in your uWSGI settings::

    http-websockets = true


Websocket and reverse proxy services
------------------------------------

Reverse proxy services, like CloudFlare <https://support.cloudflare.com/hc/en-us/articles/200169466-Can-I-use-CloudFlare-with-WebSockets->`_, might give only limited or no support for websockets. This may manifest itself in the form of *400 Bad Request* responses from the server because the reverse proxy service strips out ``Connection: Upgrade`` HTTP Request header. In this case it is recommended that you serve websockets from a separate domain where the websocket connection gets unhindered access to your server.

You need to

* Configure your naked web server to respond to an alternative domain name (``ws.example.com``)

* Configure ``pyramid_notebook`` to rewrite notebook URLs to come from the alternative domain::

    pyramid_notebook.alternative_domain = https://ws.example.com

Architecture
============

Each Pyramid user has a named Notebook process. Each Notebook process gets their own working folder, dynamically created upon the first lanch. Notebooks are managed by ``NotebookManager`` class which detects changes in notebook context and restarts the Notebook process for the user with a new context if needed.

Notebook bind itselfs to localhost ports. Pyramid view proxyes ``/notebook/`` HTTP requests to Notebook and first checks the HTTP request has necessary permissions by performing authentication and authorization checks. The proxy view is also responsible for starting a web server specific websocket proxy loop.

Launched Notebook processes are daemonized and separated from the web server process. The communication between the web server and the daemon process happens through command line, PID file and context file (JSON dump of notebook context parameters, as described above).

Local deployment
----------------

.. image :: docs/localhost_deployment.png


Production deployment
---------------------

.. image :: docs/production_deployment.png


Scalability
===========

The tool is intended for team internal use only. The default settings limit the number of users who can create and access notebooks to 10 people.

Currently a new daemon process is launched for each user in non-scalable manner. If 100+ users scalability is required there exist seveal ways to make the tool more lightweight.

Security
========

With great power comes great responsibility.

.. note::

    Giving a user *pyramid_notebook* access is equal to giving him/her SSH access to a website UNIX user.

*pyramid_notebook* relies on user authorization and authentication by Pyramid web framework. It is your site, so the authentication and authorization system is as good as you made it to be. If you do not feel comfortable exposing this much of power over website authentication, you can still have notebook sessions e.g. over SSH tunneling.

Below are some security matters you should consider.

HTTPS only
----------

*pyramid_notebook* accepts HTTPS connections only. HTTP connections are unencrypted and leaking information over HTTP could lead severe compromises.

VPN restrictions
----------------

You can configure your web server to allow access to */notebook/* URLs from whitelisted IP networks only.

Access restricted servers
-------------------------

You do not need to run *pyramid_notebook* sessions on the main web servers. You can configure a server with limited data and code separately for running *pyramid_notebook*.

The access restricted server can have

* Read-only account on the database

* Source code and configuration files containing sensitive secrets removed (HTTPS keys, API tokens, etc.)

Linux containerization
----------------------

Notebook process can be made to start inside Linux container. Thus, it would still run on the same server, but you can limit the access to file system and network by the kernel. `Read more about Linux cgroups <http://en.wikipedia.org/wiki/Cgroups>`_.

Two-factor authentication
-------------------------

Consider requiring your website admins to use `two-factor authentication <http://en.wikipedia.org/wiki/Two_factor_authentication>`_ to protect against admin credential loss due to malware, keylogging and such nasties. Example `two-factor library for Python <http://code.thejeshgn.com/pyg2fa>`_.

Troubleshooting
===============

Taking down loose notebooks
---------------------------

In the case the notebook daemon processes get stuck, e.g. by user starting a infinite loop and do not terminate properly, you can take them down.

* Any time you launch a notebook with different context (different parameters) for the user, the prior notebook process gets terminated forcefully

* You can manually terminate all notebook processes. Ex::

    pkill -f notebook_daemon.py

Crashing Notebooks
------------------

The following are indication of crashed Notebook process.
The following page on Notebook when you try try to start Notebook through web:

    Apparently IPython Notebook daemon process is not running for user

... or the IPython Notebook dialog *Connecting failed* and connecting to kernel does not work.

Notebook has most likely died because of Python exception. There exists a file ``notebook.stderr.log``, one per each user, where you should be able to read traceback what happened.

Debugging Notebook daemon
-------------------------

The notebook daemon can be started from a command line and supports normal UNIX daemon ``start``, ``stop`` and ``fg`` commands. You need to give mandatory pid file, working folder, HTTP port and kill timeout arguments.

Example how to start Notebook daemon manually::

    python $SOMEWHERE/pyramid_notebook/server/notebook_daemon.py fg /tmp/pyramid_notebook/$USER/notebook.pid /tmp/pyramid_notebook/$USER 8899 3600


Seeing startup script exceptions
--------------------------------

If the startup script does not populate your Notebook with default variables as you hope, you can always do

* ``print(locals())`` to see what local variables are set

* ``print(gocals())`` to see what global variables are set

* Manually execute startup script inside IPython Notebook, e.g. ``exec(open("/private/tmp/pyramid_notebook/user-1/.ipython/profile_default/startup/startup.py").read())``

Development
===========

* `Source code <https://bitbucket.org/miohtama/pyramid_notebook>`_

* `Issue tracker <https://bitbucket.org/miohtama/pyramid_notebook>`_

* `Documentation <https://bitbucket.org/miohtama/pyramid_notebook>`_

Tests
-----

.. note ::

    Due to complexity of IPython Notebook interaction browser tests must be executed with full Firefox or Chrome driver.

Install test dependencies::

    pip install -e ".[test]"

Running single test::

     py.test tests/* --splinter-webdriver=firefox --splinter-make-screenshot-on-failure=false --ini=pyramid_notebook/demo/development.ini -s -k test_notebook_template

Run full test coverage::

    py.test tests/* --cov pyramid_notebook --cov-report xml --splinter-webdriver=firefox --splinter-make-screenshot-on-failure=false --ini=pyramid_notebook/demo/development.ini -s -k test_notebook_template

Running uWSGI server with websockets::

    uwsgi --virtualenv=venv --wsgi-file=pyramid_notebook/demo/wsgi.py --pythonpath=venv/bin/python uwsgi.ini

Running uWSGI under Nginx for manual websocket proxy testing (OSX)::

    pkill nginx ; nginx -c `pwd`/nginx.conf
    uwsgi --virtualenv=venv --wsgi-file=pyramid_notebook/demo/wsgi.py --pythonpath=venv/bin/python uwsgi-under-nginx.ini

Related work
------------

* https://github.com/Carreau/IPython-notebook-proxy

* https://github.com/UnataInc/ipydra/tree/master/ipydrar