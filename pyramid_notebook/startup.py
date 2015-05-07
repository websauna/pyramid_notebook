"""Helpers to set up Notebook startup imports and contexts."""


def make_startup(notebook_context):
    nc = notebook_context

    add_greeting(nc, "Note: default.ipynb notebook will be cleared upon exit - do not save\n\n")
    add_greeting(nc, "Available variables and functions:\n")



    add_script(nc, "import datetime")
    add_greeting(nc, "* **datetime** - Python datetime - https://docs.python.org/3.5/library/datetime.html")

    add_script(nc, "import time")
    nc["greeting"] += "* **time** - Python time- https://docs.python.org/3.5/library/time.html\n"

    try:
        import transaction

        nc["startup"] += "import transaction\n"
        nc["greeting"] += "* **transaction** - Zope transaction manager, e.g. transaction.commit()\n"

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
