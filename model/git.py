import os

from backends import Git
import ioutils
import utils

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


class Branch(object):
    """
    name            maint
    longname        maint                       (Local)
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
        self.name = name and name or 'origin'
        self.is_canonical = False
        self.urls = {}


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

    ### Commands

    def cmd_pull(self):
        ioutils.action_preface('Trying to pull %s' % self.path)

        success = None
        if not os.path.exists(self.path):
            success = Git.clone(self.path, self._atts['url'])
        else:
            self.set_remotes_in_checkout()
            success = Git.pull(self.path)

        if success:
            ioutils.action_succeeded('Finished pulling %s' % self.path)
        else:
            ioutils.action_failed('Failed pulling %s' % self.path)
        return success

    def cmd_fetch(self):
        ioutils.action_preface('Trying to fetch %s' % self.path)

        if not os.path.exists(self.path):
            self.do_init_repo()

        success = True
        for remote in self.remotes.values():
            success = success and Git.fetch(self.path, remote.name)

        if success:
            ioutils.action_succeeded('Finished fetching %s' % self.path)
        else:
            ioutils.action_failed('Failed fetching %s' % self.path)
        return success
