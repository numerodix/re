from backends import Git
import utils

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
        self.remotes = {}

    @classmethod
    def from_cfg_attributes(cls, path, attributes):
        repo = GitRepo(path)
        for key, val in attributes.items():
            parts = key.split('.')
            name, key = None, parts[0]
            if len(parts) == 2:
                name, key = parts

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
                att = '%s.%s' % (remote.name, att)
                yield att, val


    @classmethod
    def from_checkout(cls, path):
        repo = GitRepo(path)

        names = Git.get_remotes(path)
        for name in names:
            remote = Remote(name)
            repo.remotes[name] = remote

            for url in ['url', 'pushurl']:
                key = 'remote.%s.%s' % (name, url)
                val = Git.get_conf_key(path, key)
                if val:
                    remote.urls[url] = val

        return repo
