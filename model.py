import collections
import logging
import os
import re

from backends import Git
from consts import *
import ioutils

log = logging

VCS_DIRS = (
    '.bzr',
    '.cvs',
    '.git',
    '.hg',
    '.svn',
)

class Repo(object): pass

class GitRepo(Repo):
    tag = 'git'
    vcs_dir = '.git'

    def __init__(self, repo_path, **attributes):
        self.repo_path = repo_path
        self.active = False

        url, pushurl = None, None
        if attributes:
            url = attributes.get('url', None)
            pushurl = attributes.get('pushurl', None)
        else:
            url, pushurl = self._get_repo_urls()

        self._atts = collections.OrderedDict()
        if url:
            self._atts['url'] = url
        if pushurl:
            self._atts['pushurl'] = pushurl

    def _get_repo_urls(self):
        urls = []
        for urltype in ['url', 'pushurl']:
            conf_item = 'remote.origin.%s' % urltype
            url = Git.get_conf_key(self.repo_path, conf_item)
            urls.append(url)
        return urls[0], urls[1]

    def _set_repo_urls(self):
        for urltype in ['url', 'pushurl']:
            val = self._atts.get(urltype, None)
            if val:
                conf_item = 'remote.origin.%s' % urltype
                Git.set_conf_key(self.repo_path, conf_item, val)

    def checkout_exists(self):
        if os.path.exists(os.path.join(self.repo_path, '.git')):
            return True

    def cmd_pull(self):
        ioutils.action_preface('Trying to pull %s' % self.repo_path)

        success = None
        if not os.path.exists(self.repo_path):
            success = Git.clone(self.repo_path, self._atts['url'])
        else:
            self._set_repo_urls()
            success = Git.pull(self.repo_path, self._atts['url'])

        if success:
            ioutils.action_succeeded('Finished pulling %s' % self.repo_path)
        else:
            ioutils.action_failed('Failed pulling %s' % self.repo_path)
        return success

    def attributes(self):
        for att, val in self._atts.items():
            yield att, val


class RepoManager(object):
    repotypes = [GitRepo]

    def __init__(self):
        self.repos = collections.OrderedDict()

    def find_repos(self, cwd, max_depth=None):
        def clear_list(lst):
            while True:
                try: lst.pop()
                except IndexError: break

        def at_location(relpath, dirs, files):
            depth = len(relpath.split(os.sep)) - 1

            for d in dirs:
                repotype = dispatch.get(d)
                if repotype:
                    relpath_stripped = re.sub(r'^\./', '', relpath)
                    repo = repotype(relpath_stripped)
                    if list(repo.attributes()):
                        dct[repo.repo_path] = repo

                # don't traverse vcs dirs
                if d in VCS_DIRS:
                    dirs.remove(d)

            # reached recursion depth
            if max_depth and max_depth <= depth:
                clear_list(dirs)

            # reached marker
            if depth > 0 and REPO_CONFIG in files:
                clear_list(dirs)

        dispatch = {}
        for repotype in self.repotypes:
            dispatch[repotype.vcs_dir] = repotype

        dct = {}
        for relpath, dirs, files in os.walk(cwd):
            log.debug('Scanning %s' % relpath)
            at_location(relpath, dirs, files)

        for k in sorted(dct):
            self.repos[k] = dct[k]

    def _mk_repo_id(self, tag, repo_path):
        return '%s:%s' % (tag, repo_path)

    def _split_repo_id(self, repo_id):
        for repo_type in self.repotypes:
            m = re.search(r'^(%s):(.*)$' % repo_type.tag, repo_id)
            if m:
                return repo_type, m.group(2)

    def add_repo(self, repo_id, **attributes):
        repo_type, repo_path = self._split_repo_id(repo_id)
        repo = repo_type(repo_path, **attributes)
        self.repos[repo_path] = repo

    def activate(self, repo_paths):
        for repo_path in repo_paths:
            if repo_path in self.repos:
                self.repos[repo_path].active = True

    def activate_all(self):
        for _, repo in self.repos.items():
            repo.active = True

    def items(self):
        for repo_path, repo in self.repos.items():
            repo_id = self._mk_repo_id(repo.tag, repo_path)
            yield repo_id, repo

    def active_repos(self):
        for _, repo in self.repos.items():
            if repo.active:
                yield repo
