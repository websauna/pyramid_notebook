"""Helpers to set up Notebook startup imports and contexts."""


def make_startup(notebook_context):

    # Set up some default imports and variables

    nc = notebook_context

    add_greeting(nc, "Note: default.ipynb notebook will be cleared upon exit - do not save")
    add_greeting(nc, "Available variables and functions:")

    add_script(nc, "import datetime")
    add_greeting(nc, "* **datetime** - Python datetime - https://docs.python.org/3.5/library/datetime.html")

    add_script(nc, "import time")
    add_greeting(nc, "* **time** - Python time- https://docs.python.org/3.5/library/time.html")

    try:
        import transaction

        add_script(nc,  "import transaction\n")
        add_greeting(nc, "* **transaction** - Zope transaction manager, e.g. transaction.commit()")

    except ImportError:
        pass


def add_script(nc, line):
    """Add one-liner script or several lines (newline separated)"""

    assert type(nc) == dict

    nc["startup"] = nc.get("startup") or ""

    if not nc["startup"].endswith("\n"):
        nc["startup"] += "\n"
    nc["startup"] += line + "\n"


def add_greeting(nc, line):
    """Add one-liner script or several lines (newline separated)"""

    assert type(nc) == dict

    nc["greeting"] = nc.get("greeting") or ""

    # Markdown hard line break is two new lines
    if not nc["greeting"].endswith("\n\n"):
        nc["greeting"] += "\n\n"
    nc["greeting"] += line + "\n\n"
