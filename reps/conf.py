from __future__ import absolute_import

import os
import re
import string

from reps.compat import OrderedDict
from reps.model import RepoManager


class Conf(object):
    @classmethod
    def write_config(cls, repo_manager, filepath=None, filehandle=None):
        ss = []
        for repo_name, repo in sorted(repo_manager.items()):
            ss.append('[%s]' % repo_name)
            for k, v in repo.attributes_to_cfg():
                ss.append('    %s = %s' % (k, v))

        s = '\n'.join(ss) + '\n'
        if filehandle:
            filehandle.write(s)
        else:
            with open(filepath, 'wb') as fp:
                fp.write(s.encode())

    @classmethod
    def read_config(cls, filepath):
        lines = open(filepath).readlines()
        repo_manager = RepoManager()

        dct = OrderedDict()
        cur_section = None
        for line in lines:
            if line.startswith('['):
                section = re.findall(r'^\[(.*?)\]$', line)[0]
                cur_section = section.strip()
            elif line.startswith(' '):
                key, val = re.findall(r'^[ ]{4}([^ ]+)\s*=\s*([^ ]+)$', line)[0]
                if not cur_section in dct:
                    dct[cur_section] = OrderedDict()
                dct[cur_section][key.strip()] = val.strip()

        for section, d in dct.items():
            repo_manager.add_repo(section, d)
        return repo_manager

class LocalConf(object):
    @classmethod
    def items(cls, filepath):
        if not os.path.exists(filepath):
            return []
        with open(filepath) as fp:
            return sorted(map(string.strip, fp.readlines()))
