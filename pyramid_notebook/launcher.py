import shutil
import subprocess
import psutil
import os
import logging
import time

from . import daemon

logger = logging.getLogger(__name__)


class Launcher:
    """Launch processes of which we later retrieve and terminate by known tag.

    Each process is marked by a known full command path and command line tag parameter (usually username). The tag can only create one process.

    The launched processes are fully detached.

    TODO: Add PID file management. More sensible than argument tagging.
    """

    def __init__(self, cmd, tag_arg, arg_factory=None):
        self.tag_arg = tag_arg

        self.arg_factory= arg_factory

        full_cmd = shutil.which(cmd)

        # Resolve symbolic links
        full_cmd = os.path.realpath(os.path.abspath(os.path.realpath(full_cmd)))

        if not full_cmd:
            raise RuntimeError("Could not find command {}".format(cmd))

        self.full_cmd = full_cmd

    def find_proc_by_tag(self, full_cmd, tag_arg):
        """Find a process which has a known launch command and known command line argument.

        :param full_cmd: Full path to the executed command
        """

        assert tag_arg

        for proc in psutil.process_iter():
            try:

                cmdline = proc.cmdline()

                # Checking the cmdline arg 0 did not turn out as I wanted as on OSX Python cmd gets replaced and it's not a symlink
                # /opt/local/Library/Frameworks/Python.framework/Versions/3.4/Resources/Python.app/Contents/MacOS/Python
                # /opt/local/Library/Frameworks/Python.framework/Versions/3.4/bin/python3.4

                # if cmdline and cmdline[0] != full_cmd:
                #    # Some other process, not one we are looking or
                #    continue

                if tag_arg in cmdline:
                    return proc
            except psutil.Error:
                # The process owned by different user, cannot access command line
                pass

        return None

    def get_or_spawn_process(self, force_respawn=False):
        """
        :return: tuple (psutil.Process, created_flag)
        """
        proc = self.find_proc_by_tag(self.full_cmd, self.tag_arg)

        if proc:
            if force_respawn:
                # Kill existing
                proc.kill()
            else:
                return proc, False

        self.spawn_detached()
        time.sleep(0.2)

        proc = self.find_proc_by_tag(self.full_cmd, self.tag_arg)

        assert proc, "Could not spawn and find the process with a tag. {} {}".format(self.full_cmd, self.tag_arg)

        return proc, True

    def spawn_detached(self):
        """Spawn a new process and detach it from the current process.

        TODO: PID file management anyone?
        """
        assert self.tag_arg
        assert len(self.tag_arg) > 6, "Let's at least pretend it is unique"
        other_args = self.arg_factory() if self.arg_factory else []
        args = [self.full_cmd, self.tag_arg] + other_args
        daemon.spawn_detached(self.full_cmd, args)



# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.
def which(name, flags=os.X_OK):
    """Search PATH for executable files with the given name.

    On newer versions of MS-Windows, the PATHEXT environment variable will be
    set to the list of file extensions for files considered executable. This
    will normally include things like ".EXE". This fuction will also find files
    with the given name ending with any of these extensions.

    On MS-Windows the only flag that has any meaning is os.F_OK. Any other
    flags will be ignored.

    @type name: C{str}
    @param name: The name for which to search.

    @type flags: C{int}
    @param flags: Arguments to L{os.access}.

    @rtype: C{list}
    @param: A list of the full paths to files found, in the
    order in which they were found.
    """
    result = []
    exts = filter(None, os.environ.get('PATHEXT', '').split(os.pathsep))
    path = os.environ.get('PATH', None)
    if path is None:
        return []
    for p in os.environ.get('PATH', '').split(os.pathsep):
        p = os.path.join(p, name)
        if os.access(p, flags):
            result.append(p)
        for e in exts:
            pext = p + e
            if os.access(pext, flags):
                result.append(pext)
    return result

