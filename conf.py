import ConfigParser
import collections
import os
import string
import sys

from model import RepoManager

class Conf(object):
    @classmethod
    def write_config(cls, repo_manager, filepath=None, filehandle=None):
        config = ConfigParser.ConfigParser()
        for repo_name, repo in sorted(repo_manager.items()):
            config.add_section(repo_name)
            for k, v in repo.attributes_to_cfg():
                config.set(repo_name, k, v)
                config.set(repo_name, k, v)

        if filehandle:
            config.write(filehandle)
        else:
            with open(filepath, 'wb') as fp:
                config.write(fp)

    @classmethod
    def read_config(cls, filepath):
        config = ConfigParser.ConfigParser()
        config.readfp(open(filepath))
        repo_manager = RepoManager()
        for section in config.sections():
            dct = collections.OrderedDict()
            for item in config.items(section):
                k, v = item
                dct[k] = v
            repo_manager.add_repo(section, dct)
        return repo_manager

class LocalConf(object):
    @classmethod
    def items(cls, filepath):
        if not os.path.exists(filepath):
            return []
        with open(filepath) as fp:
            return sorted(map(string.strip, fp.readlines()))
