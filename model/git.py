import logging
import os

from backends import Git
from consts import CANONICAL_REMOTE
import ioutils
import utils

log = logging

class StrFmt(object):
    @classmethod
    def split_cfg_key(cls, key):
        parts = key.split('.')
        name, url = None, parts[0]
        if len(parts) == 2:
            name, url = parts
        return name, url

    @classmethod
    def fmt_cfg_key(cls, name, url):
        return '%s.%s' % (name, url)

    @classmethod
    def fmt_remote_key(cls, name, url):
        return 'remote.%s.%s' % (name, url)

    @classmethod
    def split_branch_longname(cls, name):
        return name.split('/')


class Branch(object):
    """
    name            maint
    longname        maint                       (Local)
    is_active       False
                    remotes/origin/maint        (RemoteTracking)
                    refs/heads/maint            (Remote)
    type            Local | RemoteTracking | Remote
    is_tracking     (only for Local)
    remote          (only for RemoteTracking, Remote)

    is_behind(other)   : bool
    is_ahead_of(other) : bool
    track(other)


    query remote branches: git ls-remote origin
    """

class BranchLocal(Branch):
    def __init__(self, name, is_active):
        self.name = name
        self.is_active = is_active
class BranchRemoteTracking(Branch):
    def __init__(self, remote, longname, name):
        self.remote = remote
        self.longname = longname
        self.name = name
class BranchRemote(Branch):
    def __init__(self, remote, longname, name):
        self.remote = remote
        self.longname = longname
        self.name = name

class Remote(object):
    """
    name            origin
    is_canonical    True
    urls        [
                    url         git://github.com/numerodix/django-couchdb-utils.git
                    pushurl     git@github.com:numerodix/django-couchdb-utils.git
                ]
    branches    [
                    master
                    maint
                ]
    """

    def __init__(self, name=None):
        self.name = name and name or CANONICAL_REMOTE
        self.is_canonical = False
        self.urls = {}
        self.branches_tracking = {}
        self.branches_remote = {}


class GitRepo(object):
    """
    path                lib/backuptools
    is_active           False
    remotes         [
                        origin
                        github
                    ]

    is_checked_out()    True
    """

    vcs_tag = 'git'
    vcs_dir = '.git'

    def __init__(self, path):
        self.path = path
        self.is_active = False
        self.remotes = {}
        self.branches = {}

    ### To and from cfg

    @classmethod
    def from_cfg_attributes(cls, path, attributes):
        repo = GitRepo(path)
        for key, val in attributes.items():
            name, key = StrFmt.split_cfg_key(key)

            remote = Remote(name)
            if not repo.remotes:  # this is the first remote
                remote.is_canonical = True 
            if not remote.name in repo.remotes:
                repo.remotes[remote.name] = remote

            remote = repo.remotes[remote.name]
            remote.urls[key] = val
        return repo

    def attributes_to_cfg(self):
        names = self.remotes.keys()
        names.sort()

        # find canonical remote
        remotes = filter(lambda r: r.is_canonical, self.remotes.values())
        if remotes:
            name = remotes[0].name
            names = utils.sort_with_elem_as_first(name, names)

        for key in names:
            remote = self.remotes[key]

            urls = remote.urls.keys()
            urls = utils.sort_with_elem_as_first('url', urls)

            for att in urls:
                val = remote.urls[att]
                att = StrFmt.fmt_cfg_key(remote.name, att)
                yield att, val

    ### To and from checkout

    @classmethod
    def from_checkout(cls, path):
        repo = GitRepo(path)

        names = Git.get_remotes(path)
        for name in names:
            remote = Remote(name)
            repo.remotes[name] = remote

            for url in ['url', 'pushurl']:
                key = StrFmt.fmt_remote_key(name, url)
                val = Git.get_conf_key(path, key)
                if val:
                    remote.urls[url] = val

        return repo

    def set_remotes_in_checkout(self):
        # remove remotes not in model
        remotes_names = Git.get_remotes(self.path)
        names = filter(lambda n: n not in self.remotes, remotes_names)
        for name in names:
            Git.remove_remote(self.path, name)

        # add remotes not in checkout
        names = filter(lambda n: n not in remotes_names, self.remotes.keys())
        for name in names:
            Git.add_remote(self.path, name, self.remotes[name].urls['url'])

        # overwrite urls in checkout
        for remote in self.remotes.values():
            for key, val in remote.urls.items():
                key = StrFmt.fmt_remote_key(remote.name, key)
                Git.set_conf_key(self.path, key, val)

    ### Queries

    def is_checked_out(self):
        if os.path.exists(os.path.join(self.path, '.git')):
            return True

    ### Service methods

    def do_init_repo(self):
        os.mkdir(self.path)
        Git.repo_init(self.path)
        self.set_remotes_in_checkout()

    def get_canonical_remote(self):
        remote = None
        for r in self.remotes.values():
            if r.is_canonical:
                remote = r

        if not remote:
            remotes = filter(lambda r: r.name == CANONICAL_REMOTE, self.remotes.keys())
            if remotes:
                remote = self.remotes[remotes[0]]

        if not remote:
            remote = self.remotes[self.remotes.keys()[0]]

        return remote

    def detect_branches(self):
        for is_active, name in Git.get_branches_local(self.path):
            branch = BranchLocal(name, is_active)
            self.branches[name] = branch

        for longname in Git.get_branches_remote_tracking(self.path):
            if 'HEAD' in longname:  # special case
                continue
            remote, name = StrFmt.split_branch_longname(longname)
            remote = self.remotes[remote]
            branch = BranchRemoteTracking(remote, longname, name)
            remote.branches_tracking[name] = branch

        for remote in self.remotes.values():
            for longname in Git.get_branches_remote(self.path, remote.name):
                if 'HEAD' in longname:  # special case
                    continue
                _, _, name = StrFmt.split_branch_longname(longname)
                branch = BranchRemote(remote, longname, name)
                remote.branches_remote[name] = branch

        log.debug(self.print_branches())

    def print_branches(self):
        def fmt(remote, cls, branch):
            name, _ = branch
            type = cls.__name__
            return '%-14.14s   %-25.25s   %s\n' % (remote, name, type)

        s = ''
        for br in self.branches.items():
            s += fmt('local', BranchLocal, br)
        for r in self.remotes.values():
            for br in r.branches_tracking.items():
                s += fmt(r.name, BranchRemoteTracking, br)
            for br in r.branches_remote.items():
                s += fmt(r.name, BranchRemote, br)
        s = 'Branches:\n' + s
        return s.strip()

    def remove_stale_remote_tracking_branches(self):
        for remote in self.remotes.values():
            for tracking in remote.branches_tracking:
                if not tracking in remote.branches_remote:
                    ioutils.inform(\
                       'Removing stale remote tracking branch %s' % tracking, minor=True)
                    Git.remove_remote_tracking_branch(self.path, remote.name,
                                                      tracking)

    def setup_local_tracking_branches(self):
        remote = self.get_canonical_remote()
        for tracking in remote.branches_tracking:
            if tracking not in self.branches:
                ioutils.inform('Setting up local tracking branch %s' % tracking,
                               minor=True)
                Git.add_local_tracking_branch(self.path, remote.name, tracking)

    def merge_local_tracking_branches(self):
        save_commit = Git.get_checked_out_commit(self.path)

        clean, stashed = True, False
        if not Git.repo_is_clean(self.path):
            if Git.stash(self.path):
                ioutils.inform('Repo is dirty, stashed at %s' % save_commit, minor=True)
                stashed = True
            else:
                clean = False

        if clean:
            for branch in self.branches.values():
                if Git.checkout(self.path, branch.name):
                    print Git.get_checked_out_commit(self.path)

        if save_commit:
            if Git.checkout(self.path, save_commit):
                if stashed and Git.stash(self.path, apply=True):
                    ioutils.inform('Restored %s' % save_commit, minor=True)

    ### Commands

    def cmd_fetch(self):
        ioutils.inform('Fetching %s' % self.path)

        if not os.path.exists(self.path):
            self.do_init_repo()

        success = True
        for remote in self.remotes.values():
            success = success and Git.fetch(self.path, remote.name)

        if not success:
            ioutils.complain('Failed fetching %s' % self.path)
        return success

    def cmd_merge(self):
        ioutils.inform('Merging %s' % self.path)

        success = True
        self.detect_branches()
        self.remove_stale_remote_tracking_branches()
        self.setup_local_tracking_branches()
        self.merge_local_tracking_branches()

        if not success:
            ioutils.complain('Failed merging %s' % self.path)
