Embed IPython Notebook shell on your Pyramid web site.

Run demo
---------------------------------

* Checkout repository

* Install deps and package::

    python setup.py develop

* Run demo::

    pserve demo/development.ini

Visit at `http://localhost:9000 <http://localhost:9000>`_.

Try accounts is *user* / *password* and *user2* / *password*

Kill all notebooks on the server
---------------------------------

Ex::

    pkill -f notebook_daemon.py