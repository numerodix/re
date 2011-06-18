#!/usr/bin/env python

import collections
import logging
import optparse
import os
import re
import sys

from conf import Conf, LocalConf
from consts import *
from model import RepoManager
import ioutils


class Program(object):
    def cmd_list(self, depth=None, update=False):
        repo_manager = RepoManager()
        repo_manager.find_repos('.', max_depth=depth)

        Conf.write_config(repo_manager, filehandle=sys.stdout)
        if update:
            Conf.write_config(repo_manager, filepath=REPO_CONFIG)
            ioutils.inform('Wrote %s' % REPO_CONFIG)
        else:
            ioutils.suggest('Run with -u to update %s' % REPO_CONFIG)

    def cmd_pull(self):
        repo_manager = Conf.read_config(REPO_CONFIG)
        #Conf.write_config(repo_manager, filehandle=sys.stdout)
        #return

        local_repos = LocalConf.items(REPO_CONFIG_LOCAL)
        if local_repos:
            repo_manager.activate(local_repos)
        else:
            repo_manager.activate_all()

        # dry run first
        clean = True
        for repo in repo_manager.active_repos():
            if not repo.is_checked_out() and os.path.exists(repo.path):
                ioutils.complain("Cannot pull '%s', path exists" % repo.path)
                clean = False

        if clean:
            for repo in repo_manager.active_repos():
                repo.cmd_fetch()



if __name__ == '__main__':
    usage = ['%s [command]' % os.path.basename(sys.argv[0])]
    usage.append('\nCommands:')
    usage.append('  list [-d 1] [-u]   List repositories')
    usage.append('  pull               Pull repositories')
    usage = '\n'.join(usage)
    optparser = optparse.OptionParser(usage=usage)
    optparser.add_option('-d', '--depth', action='store', type="int", help='Recurse to depth')
    optparser.add_option('-u', '--update', action='store_true', help='Update %s' % REPO_CONFIG)
    optparser.add_option('-v', '--verbose', action='store_true', help='Print debug output')
    (options, args) = optparser.parse_args()

    def print_help():
        optparser.print_help()
        sys.exit(2)

    try:
        cmd = args[0]
    except IndexError:
        print_help()

    def set_log_params(verbose=False):
        logfmt = '%(levelname)s: %(message)s'
        level = logging.DEBUG if verbose else logging.ERROR
        logging.basicConfig(format=logfmt, level=level)
    set_log_params(verbose=options.verbose)

    program = Program()
    if cmd == 'list':
        program.cmd_list(depth=options.depth, update=options.update)
    elif cmd == 'pull':
        program.cmd_pull()
    else:
        print_help()
