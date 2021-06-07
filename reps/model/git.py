from __future__ import absolute_import

import logging
import os

from reps import ioutils
from reps import utils
from reps.backends import Git
from reps.consts import CANONICAL_REMOTE
from reps.model.gitstrings import StrFmt

logger = logging


class Branch(object):
    @classmethod
    def all_branches(cls, repo):
        for branch in repo.branches.values():
            yield branch
        for remote in repo.remotes.values():
            for branch in remote.branches_tracking.values():
                yield branch

    @classmethod
    def print_branches(cls, repo):
        def fmt(branch):
            remote = getattr(branch, 'remote', None)
            if remote:
                remote = remote.name
            else:
                remote = 'local'
            if not branch.exists:
                remote = '-%s' % remote
            name = branch.name
            if getattr(branch, 'tracking', None):
                name = '%-15.15s -> %s/%s' % (branch.name,
                                              branch.tracking.remote.name,
                                              branch.tracking.name)
            type = branch.__class__.__name__
            return '%-10.10s   %-40.40s   %s\n' % (remote, name, type)

        s = ''
        for branch in Branch.all_branches(repo):
            s += fmt(branch)
        s = 'Branches:\n' + s
        return s.strip()

    @classmethod
    def check_heartbeats(cls, repo):
        for branch in cls.all_branches(repo):
            branch.check_exists()

        logger.debug(cls.print_branches(repo))

class BranchLocal(Branch):
    def __init__(self, repo, name):
        self.repo = repo
        self.name = name

        self.exists = True
        self.tracking = None

    def detect_tracking(self):
        remote_pointer = StrFmt.fmt_branch_remote_pointer(self.name)
        merge_pointer = StrFmt.fmt_branch_merge_pointer(self.name)
        rem_name = Git.get_conf_key(self.repo.path, remote_pointer)
        longname = Git.get_conf_key(self.repo.path, merge_pointer)

        if rem_name and longname:
            _, _, br_name = StrFmt.split_branch_longname(longname, parts=3)

            remote = Remote.get_remote(self.repo, rem_name)
            branch = BranchRemoteTracking.get_branch(self.repo, remote, longname,
                                                     br_name)

            branch.tracked_by = self
            self.tracking = branch

            logger.info('Detected local tracking branch %s on %s/%s' %
                        (self.name, rem_name, br_name))

    def check_exists(self):
        found = False
        for name in Git.get_branches_local(self.repo.path):
            if self.name == name:
                found = True
        self.exists = found

    def is_checked_out(self):
        return self.name == Git.get_checked_out_commit(self.repo.path)

    @classmethod
    def cmd_add_tracking(cls, repo, track_branch):
        if Git.add_local_tracking_branch(repo.path, track_branch.remote.name,
                                         track_branch.name):
            branch = cls.get_branch(repo, track_branch.name)
            branch.tracking = track_branch

    def cmd_set_tracking(self, track_branch):
        remote_pointer = StrFmt.fmt_branch_remote_pointer(track_branch.name)
        merge_pointer = StrFmt.fmt_branch_merge_pointer(track_branch.name)
        rem_name = Git.set_conf_key(self.repo.path, remote_pointer,
                                    track_branch.remote.name)
        longname = Git.set_conf_key(self.repo.path, merge_pointer,
                                    StrFmt.fmt_branch_longname(track_branch.name))

    def cmd_remove(self):
        if Git.remove_local_branch(self.repo.path, self.name):
            if self.tracking:
                self.tracking.tracked_by = None
            del(self.repo.branches[self.name])

    def cmd_checkout(self):
        if Git.checkout(self.repo.path, self.name):
            return True

    def cmd_merge(self, branch):
        longname = StrFmt.fmt_branch_remote_tracking(branch.remote.name, branch.name)
        if Git.commit_is_ahead_of(self.repo.path, self.name, longname):
            ioutils.suggest('Branch %s is ahead of %s, is pushable' %
                            (self.name, longname), minor=True)
            return True
        else:
            if self.cmd_checkout():
                remoted = StrFmt.fmt_branch_remote_tracking(branch.remote.name,
                                                            branch.name)
                merge_ok, output = Git.merge(self.repo.path, remoted)
                if merge_ok:
                    if output:
                        ioutils.inform('Merged %s on %s' % (longname, self.name),
                                       minor=True)
                        ioutils.output(output)
                    return True
                else:
                    Git.reset_hard(self.repo.path, self.name)

    @classmethod
    def get_branch(cls, repo, name):
        if name not in repo.branches:
            branch = BranchLocal(repo, name)
            repo.branches[name] = branch
        branch = repo.branches[name]
        return branch

    @classmethod
    def detect_branches(cls, repo):
        found = []
        for name in Git.get_branches_local(repo.path):
            branch = BranchLocal.get_branch(repo, name)
            branch.exists = True
            found.append(name)

        for name in repo.branches:
            if not name in found:
                repo.branches[name].exists = False

class BranchRemoteTracking(Branch):
    def __init__(self, repo, remote, longname, name):
        self.repo = repo
        self.name = name
        self.remote = remote
        self.longname = longname
        self.name = name

        self.exists = True
        self.tracked_by = None

    def check_exists(self):
        found = False
        for longname in Git.get_branches_remote_tracking(self.repo.path):
            if self.longname == longname:
                found = True
        self.exists = found

    @classmethod
    def get_branch(cls, repo, remote, longname, name):
        if name not in remote.branches_tracking:
            branch = BranchRemoteTracking(repo, remote, longname, name)
            remote.branches_tracking[name] = branch
        branch = remote.branches_tracking[name]
        return branch

    @classmethod
    def detect_branches(cls, repo):
        for longname in Git.get_branches_remote_tracking(repo.path):
            if 'HEAD' in longname:  # special case
                continue
            remote, name = StrFmt.split_branch_longname(longname, parts=2)
            remote = Remote.get_remote(repo, remote)
            branch = BranchRemoteTracking.get_branch(repo, remote, longname, name)

class BranchRemote(Branch):
    pass

class Remote(object):
    def __init__(self, repo, name=None):
        self.repo = repo
        self.name = name and name or CANONICAL_REMOTE
        self.is_canonical = name == CANONICAL_REMOTE
        self.urls = {}
        self.branches_tracking = {}
        self.branches_remote = {}

    def cmd_fetch(self):
        return Git.fetch(self.repo.path, self.name)

    @classmethod
    def get_remote(cls, repo, name):
        if name not in repo.remotes:
            remote = Remote(repo, name)
            repo.remotes[name] = remote
        remote = repo.remotes[name]
        return remote

    @classmethod
    def get_canonical_remote(cls, repo):
        remote = None
        for r in repo.remotes.values():
            if r.is_canonical:
                remote = r

        if not remote:
            remotes = filter(lambda r: r.name == CANONICAL_REMOTE, repo.remotes.keys())
            if remotes:
                remote = repo.remotes[remotes[0]]

        if not remote:
            remote = repo.remotes[repo.remotes.keys()[0]]

        return remote


class GitRepo(object):
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

            remote = Remote(repo, name)
            if not repo.remotes:  # this is the first remote
                remote.is_canonical = True
            if not remote.name in repo.remotes:
                repo.remotes[remote.name] = remote

            remote = repo.remotes[remote.name]
            remote.urls[key] = val
        return repo

    def attributes_to_cfg(self):
        names = list(self.remotes.keys())
        names.sort()

        # find canonical remote
        remotes = list(filter(lambda r: r.is_canonical, self.remotes.values()))
        if remotes:
            name = remotes[0].name
            names = utils.sort_with_elem_as_first(name, names)

        for key in names:
            remote = self.remotes[key]

            urls = list(remote.urls.keys())
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
            remote = Remote(repo, name)
            repo.remotes[name] = remote

            for url in ['url', 'pushurl']:
                key = StrFmt.fmt_remote_key(name, url)
                val = Git.get_conf_key(path, key)
                if val:
                    remote.urls[url] = val

        return repo

    def set_remotes_in_checkout(self):
        logger.info('Setting remotes in checkout')

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
        logger.info('Initializing repo')

        os.makedirs(self.path)
        Git.repo_init(self.path)
        self.set_remotes_in_checkout()

    def detect_branches(self, only_remote=False, update_tracking=False):
        logger.info('Detecting branches')

        BranchRemoteTracking.detect_branches(self)
        if not only_remote:
            BranchLocal.detect_branches(self)
        if update_tracking:
            for branch in self.branches.values():
                branch.detect_tracking()

        logger.debug(Branch.print_branches(self))

    def check_for_stale_local_tracking_branches(self):
        logger.info('Checking for stale local tracking branches')

        for branch in list(self.branches.values()):
            if getattr(branch, 'tracking', None) and not branch.tracking.exists:
                if ioutils.prompt('Stale local tracking branch %s, remove?' %
                                  branch.name, minor=True):
                    # check out another branch
                    if branch.is_checked_out():
                        others = list(filter(lambda x: x != branch, self.branches.values()))
                        if not others[0].cmd_checkout():
                            continue
                    branch.cmd_remove()
                    del(self.branches[branch.name])

    def setup_local_tracking_branches(self):
        logger.info('Setting up local tracking branches')

        remote = Remote.get_canonical_remote(self)
        for branch in remote.branches_tracking.values():
            if not branch.tracked_by:
                local_branch = self.branches.get(branch.name, None)
                if local_branch:
                    ioutils.inform('Setting local branch %s to track %s/%s' %
                                   (branch.name, branch.remote.name,
                                    branch.name), minor=True)
                    local_branch.cmd_set_tracking(branch)
                else:
                    ioutils.inform('Setting up local tracking branch %s' %
                                   branch.name, minor=True)
                    BranchLocal.cmd_add_tracking(self, branch)

    def merge_local_tracking_branches(self):
        logger.info('Merging local tracking branches')

        save_commit = Git.get_checked_out_commit(self.path)
        if save_commit is None:
            ioutils.complain('Failed to get last commit for %s' % self.path)
            return

        # checkout current branch in case repo has just been cloned and workdir
        # is empty
        if not Git.repo_is_clean(self.path):
            if save_commit in self.branches:
                self.branches[save_commit].cmd_checkout()

        # if the workdir is not clean we will stash it first
        stashed = False
        if not Git.repo_is_clean(self.path):
            if Git.stash(self.path):
                ioutils.inform('Repo is dirty, stashed at %s' % save_commit, minor=True)
                stashed = True

        # merge all tracking branches
        for branch in self.branches.values():
            if branch.tracking:
                if not branch.cmd_merge(branch.tracking):
                    ioutils.complain('Merge failed at %s of %s/%s' %
                                     (branch.name, branch.tracking.remote.name,
                                      branch.tracking.name), minor=True)

        # check out the "current branch" again - so we end on the same branch
        # checked out as we had in the beginning
        if save_commit in self.branches:
            self.branches[save_commit].cmd_checkout()

        # apply the stash back onto the workdir (could create a conflict)
        if Git.checkout(self.path, save_commit):
            if stashed and Git.stash(self.path, apply=True):
                ioutils.inform('Restored stash at %s' % save_commit, minor=True)

    ### Commands

    def cmd_compact(self, check=True):
        ioutils.inform('Checking for compactness: %s' % self.path)

        def do_check(output_always=False):
            is_compact, output = Git.check_compactness_local(self.path)
            if not is_compact or output_always:
                ioutils.output(output)
            return is_compact

        is_compact = do_check()
        if not check and not is_compact:
            ioutils.inform('Trying to compact', minor=True)
            Git.compact_local(self.path)
            do_check(output_always=True)

    def cmd_fetch(self):
        ioutils.inform('Fetching %s' % self.path)

        if not os.path.exists(self.path):
            self.do_init_repo()

        success = True
        self.set_remotes_in_checkout()
        self.detect_branches(update_tracking=True)
        for remote in self.remotes.values():
            success = success and remote.cmd_fetch()
        self.detect_branches(only_remote=True)

        if not success:
            ioutils.complain('Failed fetching %s' % self.path)
        return success

    def cmd_merge(self):
        ioutils.inform('Merging %s' % self.path)

        # Check branch heartbeats after fetch
        Branch.check_heartbeats(self)

        # Branch post process
        self.check_for_stale_local_tracking_branches()
        self.setup_local_tracking_branches()

        # Merge locals
        self.merge_local_tracking_branches()
