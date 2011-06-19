import logging
import os
import re

import ioutils

log = logging

class Git(object):
    @classmethod
    def repo_init(cls, path):
        ret, out, err = ioutils.invoke(path, ['git', 'init'])
        if ret:
            log.error("Could not init repo '%s': %s" % \
                      (path, err))

    @classmethod
    def get_checked_out_commit(cls, path):
        branches = cls._get_branches_local(path)
        for active, branch in branches:
            if active:
                return branch

        ret, out, err = ioutils.invoke(path, ['git', 'log', '-n1'])
        if ret:
            log.error("Could not get checkout commit '%s': %s" % \
                      (path, err))
        else:
            m = re.match(r'^commit\s*([a-z0-9]+)', out)
            if m:
                val = m.group(1)
        return val

    @classmethod
    def repo_is_clean(cls, path):
        ret, out, err = ioutils.invoke(path, ['git', 'status', '--short'])
        if ret:
            log.error("Could not init repo '%s': %s" % \
                      (path, err))
        else:
            if out:
                lst = out.split('\n')
                lst = map(lambda s: re.match(r'^\?\?', s) and True or False, lst)
                if not all(lst):
                    return False
        return True

    @classmethod
    def commit_is_ahead_of(cls, path, first, second):
        ret1, out1, err1 = ioutils.invoke(path, ['git', 'log', first])
        if ret1:
            log.error("Could not get log for branch %s for '%s': %s" % \
                      (first, path, err1))

        ret2, out2, err2 = ioutils.invoke(path, ['git', 'log', second])
        if ret2:
            log.error("Could not get log for branch %s for '%s': %s" % \
                      (second, path, err2))

        log = re.findall(r'(?m)^commit ([a-z0-9]+)', out1)[1:]
        commit = re.findall(r'(?m)^commit ([a-z0-9]+)', out2)[0]
        if commit in log:
            return True
        return False

    @classmethod
    def stash(cls, path, apply=False):
        args = ['git', 'stash']
        if apply:
            args += ['apply']
        ret, out, err = ioutils.invoke(path, args)
        if ret:
            log.error("Could not stash repo '%s': %s" % \
                      (path, err))
        return True

    @classmethod
    def checkout(cls, path, commit):
        ret, out, err = ioutils.invoke(path, ['git', 'checkout', commit])
        if ret:
            log.error("Could not checkout %s for '%s': %s" % \
                      (commit, path, err))
        return True

    @classmethod
    def get_conf_key(cls, path, key):
        ret, val, err = ioutils.invoke(path, ['git', 'config', key])
        if ret:
            val = None
            log.warn("Could not get config key %s for '%s': %s" % \
                      (key, path, err))
        return val

    @classmethod
    def set_conf_key(cls, path, key, value):
        ret, out, err = ioutils.invoke(path, ['git', 'config', key, value])
        if ret:
            log.error("Could not set config %s=%s for '%s': %s" % \
                      (key, value, path, err))

    @classmethod
    def get_remotes(cls, path):
        ret, out, err = ioutils.invoke(path, ['git', 'remote'])
        if not out:
            val = []
            log.warn("Could not get remotes for '%s': %s" % \
                     (path, err))
        else:
            val = out.split('\n')
        return val

    @classmethod
    def remove_remote(cls, path, name):
        ret, out, err = ioutils.invoke(path, ['git', 'remote', 'rm', name])
        if ret:
            log.error("Could not remove remote %s for '%s': %s" % \
                      (name, path, err))

    @classmethod
    def _get_branches_local(cls, path):
        ret, out, err = ioutils.invoke(path, ['git', 'branch'])
        if not out:
            val = []
            log.warn("Could not get local branches for '%s': %s" % \
                     (path, err))
        else:
            lst = out.split('\n')
            val = []
            for br in lst:
                active = False
                if re.match(r'^[*] .*', br):
                    active = True
                name = re.sub(r'^[*]?\s*', '', br)
                if not re.match(r'^[(].*[)]$', name):
                    val.append( (active, name) )
        return val

    @classmethod
    def get_branches_local(cls, path):
        pairs = cls._get_branches_local(path)
        lst = map(lambda (active,name): name, pairs)
        return lst

    @classmethod
    def get_branches_remote_tracking(cls, path):
        ret, out, err = ioutils.invoke(path, ['git', 'branch', '-r'])
        if not out:
            val = []
            log.warn("Could not get remote tracking branches for '%s': %s" % \
                     (path, err))
        else:
            val = out.split('\n')
            val = map(lambda s: re.sub(r'^\s*', '', s), val)
        return val

    @classmethod
    def get_branches_remote(cls, path, remote):
        ret, out, err = ioutils.invoke(path, ['git', 'ls-remote', remote])
        if not out:
            val = []
            log.warn("Could not get remote branches for '%s': %s" % \
                     (path, err))
        else:
            lst = out.split('\n')
            val = []
            for line in lst:
                name = re.sub(r'^(?i)[a-z0-9]+\s+', '', line)
                if re.match(r'^refs/heads/.*', name):
                    val.append(name)
        return val

    @classmethod
    def remove_local_branch(cls, path, branch):
        ret, out, err = ioutils.invoke(path, ['git', 'branch', '-D', branch])
        if ret:
            log.error("Could not remove local branch %s for '%s': %s" % \
                      (branch, path, err))

    @classmethod
    def remove_remote_tracking_branch(cls, path, remote, branch):
        arg = ':refs/heads/%s' % branch
        ret, out, err = ioutils.invoke(path, ['git', 'push', remote, arg])
        if ret:
            log.error("Could not remove remote tracking branch %s/%s for '%s': %s" % \
                      (remote, branch, path, err))

    @classmethod
    def add_local_tracking_branch(cls, path, remote, branch):
        arg = '%s/%s' % (remote, branch)
        ret, out, err = ioutils.invoke(path, ['git', 'branch', '--track', branch, arg])
        if ret:
            log.error("Could not add local tracking branch %s for '%s': %s" % \
                      (branch, path, err))
        else:
            return True

    @classmethod
    def add_remote(cls, path, name, url):
        ret, out, err = ioutils.invoke(path, ['git', 'remote', 'add', name, url])
        if ret:
            log.error("Could not add remote %s=%s for '%s': %s" % \
                      (name, url, path, err))

    @classmethod
    def clone(cls, path, url):
        os.mkdir(path)
        ret, out, err = ioutils.invoke(path, ['git', 'clone', url, '.'])
        if ret:
            log.error("Clone error for '%s': %s" % (path, err))
        else:
            return True

    @classmethod
    def fetch(cls, path, name):
        ret, out, err = ioutils.invoke(path, ['git', 'fetch', '--prune', name])
        if ret:
            log.error("Fetch error for '%s' from %s: %s" % (path, name, err))
        else:
            return True

    @classmethod
    def merge(cls, path, branch):
        ret, out, err = ioutils.invoke(path, ['git', 'merge', branch])
        if ret:
            log.warn("Merge error using branch %s for '%s': %s" % (branch, path, err))
        else:
            return True

    @classmethod
    def reset_hard(cls, path, branch):
        ret, out, err = ioutils.invoke(path, ['git', 'checkout', '-f', branch])
        if ret:
            log.warn("Hard reset failed on branch %s for '%s': %s" % (branch, path, err))

    @classmethod
    def pull(cls, path):
        ret, out, err = ioutils.invoke(path, ['git', 'pull'])
        if ret:
            log.error("Pull error for '%s': %s" % (path, err))
        else:
            return True
