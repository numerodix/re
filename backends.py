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
    def get_branches_local(cls, path):
        ret, out, err = ioutils.invoke(path, ['git', 'branch'])
        if not out:
            val = []
            log.warn("Could not get branches for '%s': %s" % \
                     (path, err))
        else:
            lst = out.split('\n')
            val = []
            for br in lst:
                name = br
                active = br[:2] == '* ' and True or False
                if active:
                    name = br[2:]
                val.append( (active, name) )
        return val

    @classmethod
    def get_branches_remote_tracking(cls, path):
        ret, out, err = ioutils.invoke(path, ['git', 'branch', '-r'])
        if not out:
            val = []
            log.warn("Could not get branches for '%s': %s" % \
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
            log.warn("Could not get branches for '%s': %s" % \
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
    def remove_remote_tracking_branch(cls, path, remote, branch):
        arg = ':refs/heads/%s' % branch
        ret, out, err = ioutils.invoke(path, ['git', 'push', remote, arg])
        if ret:
            log.error("Could not remove remote tracking branch %s/%s for '%s': %s" % \
                      (remote, branch, path, err))

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
        ret, out, err = ioutils.invoke(path, ['git', 'fetch', name])
        if ret:
            log.error("Fetch error for '%s' from %s: %s" % (path, name, err))
        else:
            return True

    @classmethod
    def pull(cls, path):
        ret, out, err = ioutils.invoke(path, ['git', 'pull'])
        if ret:
            log.error("Pull error for '%s': %s" % (path, err))
        else:
            return True
