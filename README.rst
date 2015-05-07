Embed IPython Notebook shell on your Pyramid web site.

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

* Authentication integration: use the same credentials as you use for the site administration.

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

Demo
====

* Checkout source code repository::

    git clone https://miohtama@bitbucket.org/miohtama/pyramid_notebook.git

* Create virtualenv for Python 3.3. Install deps and package::

    cd pyramid_notebook
    virtualenv --python=python3.4 venv
    source venv/bin/activate
    pip install requirements.txt
    python setup.py develop

* Run demo::

    pserve demo/development.ini

Visit at `http://localhost:9999 <http://localhost:9999>`_.

Try accounts is *user* / *password* and *user2* / *password*

Installation
============

It is recommend to install using ``pip`` and ``virtualenv``. `Python guide for package installation <https://packaging.python.org/en/latest/installing.html>`_. ::

    pip install pyramid_notebook

Usage
=====

Your application needs to configure three custom views

* ``launch_ipython()`` which does authentication and authorization and calls ``pyramid_notebook.views.launch_notebook()`` to open a new Notebook for a user. ``launch_ipython()`` takes in Notebook context parameters (see below), starts a new Notebook kernel if needed and then redirects user to Notebook itself.

* ``shutdown_ipython()`` which does authentication and authorization and calls ``pyramid_notebook.views.shutdown_notebook()`` to force close a notebook for a user.

* ``notebook_proxy()`` which does authentication and authorization and calls ``pyramid_notebook.views.notebook_proxy()`` to proxy HTTP request to upstream IPython Notebook server bind to a localhost port. `notebook_proxy` is mapped to `/notebook/` path in your site URL. Both your site and Notebook upstream server should agree on this location.

For complete examples see the demo application.

Pyramid configuration parameters
--------------------------------

*python_notebook* reads following parameters from your Pyramid INI configuration file::

    # Where we store IPython Notebook runtime and persistent files
    # (pid, saved notebooks, etc.).
    # Each user will get a personal subfolder in this folder
    pyramid_notebook.notebook_folder = /tmp/pyramid_notebook

    # Automatically shutdown IPython Notebook kernel
    # after his many seconds have elapsed since startup
    pyramid_notebook.kill_timeout = 3600


Notebook context parameters
---------------------------

Opened Notebooks can be context sensitive with the following parameters. Some are filled in by the framework, some of those you can set yourself.

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


Architecture
============

Each Pyramid user has a named Notebook process. Each Notebook process gets their own working folder, dynamically created upon the first lanch. Notebooks are managed by ``NotebookManager`` which detects changes in Notebook context and restarts the Notebook for the user with new context if needed.

Notebook bind itselfs to localhost ports. Pyramid view proxyes ``/notebook/`` HTTP requestse to Notebook and first checks the HTTP request has necessary permissions by performing authentication and authorization checks.

Notebook needs both HTTP and WebSocket channels. Because Pyramid is not aware of Websockets, on a production set up (not localhost) you need to use a front end web server to take care of WebSocket proxying.

Launched Notebook processes are daemonized and separated from the web server process. The communication between the web server and the daemon process happens through command line, PID file and context file (JSON dump of notebook context parameters, as described above).


Scalability
===========

The tool is intended for team internal use only. The default settings limit the number of users who can create and access notebooks to 10 people.

Currently a new daemon process is launched for each user in non-scalable manner. If 100+ users scalability is required there exist several ways to make the tool more lightweight.

Security
========

With great power comes great responsibility.

.. note::

    Giving a user *pyramid_notebook* access is equal to giving him/her SSH access to a website UNIX user.

*pyramid_notebook* relies on user authorization and authentication by Pyramid web framework. It is your site, so the authentication and authorization system is as good as you made it to be. If you do not feel comfortable exposing this much of power over website authentication, you can still have notebook sessions e.g. over SSH tunneling.

Below are some security matters you should consider.

HTTPS only
------------------------------

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

