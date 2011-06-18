import logging
import os
import re

import ioutils

log = logging

class Git(object):
    @classmethod
    def get_conf_key(cls, repo_path, key):
        ret, val, err = ioutils.invoke(repo_path, ['git', 'config', key])
        if ret:
            val = None
            log.warn("Could not get config key %s for '%s': %s" % \
                      (key, repo_path, err))
        return val

    @classmethod
    def set_conf_key(self, repo_path, key, value):
        ret, out, err = ioutils.invoke(repo_path, ['git', 'config', key, value])
        if ret:
            log.error("Could not set config %s=%s for '%s': %s" % \
                      (key, value, repo_path, err))

    @classmethod
    def clone(cls, repo_path, url):
        os.mkdir(repo_path)
        ret, out, err = ioutils.invoke(repo_path, ['git', 'clone', url, '.'])
        if ret:
            log.error("Clone error for '%s': %s" % (repo_path, err))
        else:
            return True

    @classmethod
    def pull(cls, repo_path, url):
        ret, out, err = ioutils.invoke(repo_path, ['git', 'pull'])
        if ret:
            log.error("Pull error for '%s': %s" % (repo_path, err))
        else:
            return True
