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
    def set_conf_key(self, path, key, value):
        ret, out, err = ioutils.invoke(path, ['git', 'config', key, value])
        if ret:
            log.error("Could not set config %s=%s for '%s': %s" % \
                      (key, value, path, err))

    @classmethod
    def get_remotes(self, path):
        ret, out, err = ioutils.invoke(path, ['git', 'remote'])
        if not out:
            val = []
            log.warn("Could not get remotes for '%s': %s" % \
                     (path, err))
        else:
            val = out.split('\n')
        return val

    @classmethod
    def remove_remote(self, path, name):
        ret, out, err = ioutils.invoke(path, ['git', 'remote', 'rm', name])
        if ret:
            log.error("Could not remove remote %s for '%s': %s" % \
                      (name, path, err))

    @classmethod
    def add_remote(self, path, name, url):
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
    def pull(cls, path):
        ret, out, err = ioutils.invoke(path, ['git', 'pull'])
        if ret:
            log.error("Pull error for '%s': %s" % (path, err))
        else:
            return True
