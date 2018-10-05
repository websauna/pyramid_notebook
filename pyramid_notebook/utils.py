# Standard Library
import copy
import os
import os.path


# Courtesy of http://stackoverflow.com/questions/5884066/hashing-a-python-dictionary
def make_dict_hash(o):
    """Make a hash from a dictionary, list, tuple or set to any level, containing
    only other hashable types (including any lists, tuples, sets, and dictionaries).
    """
    if isinstance(o, (set, tuple, list)):
        return tuple([make_dict_hash(e) for e in o])
    elif not isinstance(o, dict):
        return hash(o)

    new_o = copy.deepcopy(o)
    for k, v in new_o.items():
        new_o[k] = make_dict_hash(v)

    return hash(tuple(frozenset(sorted(new_o.items()))))


class change_directory:
    """ChangeDirectory is a context manager that allows you to temporary change the working directory.

    Courtesy of http://code.activestate.com/recipes/576620-changedirectory-context-manager/
    """

    def __init__(self, directory):
        self._dir = directory
        self._cwd = os.getcwd()
        self._pwd = self._cwd

    @property
    def current(self):
        return self._cwd

    @property
    def previous(self):
        return self._pwd

    @property
    def relative(self):
        cwd = self._cwd.split(os.path.sep)
        pwd = self._pwd.split(os.path.sep)
        length = min(len(cwd), len(pwd))
        idx = 0
        while idx < length and cwd[idx] == pwd[idx]:
            idx += 1
        return os.path.normpath(os.path.join(*(['.'] + (['..'] * (len(cwd) - idx)) + pwd[idx:])))

    def __enter__(self):
        self._pwd = self._cwd
        os.chdir(self._dir)
        self._cwd = os.getcwd()
        return self

    def __exit__(self, *args):
        os.chdir(self._pwd)
        self._cwd = self._pwd


def route_to_alt_domain(request, url):
    """Route URL to a different subdomain.

    Used to rewrite URLs to point to websocket serving domain.
    """

    # Do we need to route IPython Notebook request from a different location
    alternative_domain = request.registry.settings.get("pyramid_notebook.alternative_domain", "").strip()
    if alternative_domain:
        url = url.replace(request.host_url, alternative_domain)

    return url
