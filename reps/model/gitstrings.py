from __future__ import absolute_import


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

    @classmethod
    def fmt_branch_longname(cls, name):
        return 'refs/heads/%s' % name

    @classmethod
    def fmt_branch_remote_tracking(cls, remote, branch):
        return '%s/%s' % (remote, branch)

    @classmethod
    def fmt_branch_remote_pointer(cls, branch):
        return 'branch.%s.remote' % branch

    @classmethod
    def fmt_branch_merge_pointer(cls, branch):
        return 'branch.%s.merge' % branch
