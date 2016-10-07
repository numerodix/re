from __future__ import absolute_import

import logging
import os
import re

from reps import consts
from reps import ioutils
from reps.compat import OrderedDict
from reps.model.git import GitRepo

logger = logging

VCS_DIRS = (
    '.bzr',
    '.cvs',
    '.git',
    '.hg',
    '.svn',
)


class RepoManager(object):
    repotypes = [GitRepo]

    def __init__(self):
        self.repos = OrderedDict()

    def find_repos(self, cwd, max_depth=None, excluded_dirs=None):
        excluded_dirs = excluded_dirs or []

        def clear_list(lst):
            while True:
                try:
                    lst.pop()
                except IndexError:
                    break

        def at_location(relpath, dirs, files):
            depth = len(relpath.split(os.sep)) - 1

            for d in dirs:
                repotype = dispatch.get(d)
                if repotype:
                    relpath_stripped = re.sub(r'^\./', '', relpath)
                    repo = repotype.from_checkout(relpath_stripped)
                    if repo.remotes:
                        dct[repo.path] = repo

                # don't traverse vcs dirs
                if d in VCS_DIRS or d in excluded_dirs:
                    dirs.remove(d)

            # reached recursion depth
            if max_depth and max_depth <= depth:
                clear_list(dirs)

            # reached marker
            if depth > 0 and consts.REPO_CONFIG in files:
                clear_list(dirs)

        dispatch = {}
        for repotype in self.repotypes:
            dispatch[repotype.vcs_dir] = repotype

        dct = {}
        for relpath, dirs, files in os.walk(cwd):
            logger.debug('Scanning %s' % relpath)
            at_location(relpath, dirs, files)

        for k in sorted(dct):
            self.repos[k] = dct[k]

    def _mk_repo_id(self, vcstag, path):
        return '%s:%s' % (path, vcstag)

    def _split_repo_id(self, repo_id):
        for repo_type in self.repotypes:
            m = re.search(r'^(.*):(%s)$' % repo_type.vcs_tag, repo_id)
            if m:
                return repo_type, m.group(1)

    def add_repo(self, repo_id, attributes):
        repo_type, path = self._split_repo_id(repo_id)
        repo = repo_type.from_cfg_attributes(path, attributes)
        self.repos[path] = repo

    def activate(self, paths):
        for path in paths:
            if path in self.repos:
                self.repos[path].is_active = True
            else:
                ioutils.complain("Skipping unknown repo: %s" % path)

    def activate_all(self):
        for _, repo in self.repos.items():
            repo.is_active = True

    def items(self):
        for path, repo in self.repos.items():
            repo_id = self._mk_repo_id(repo.vcs_tag, path)
            yield repo_id, repo

    def active_repos(self):
        for _, repo in self.repos.items():
            if repo.is_active:
                yield repo
