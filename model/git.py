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
    urls        [
                    url         git://github.com/numerodix/django-couchdb-utils.git
                    pushurl     git@github.com:numerodix/django-couchdb-utils.git
                ]
    is_canonical    True
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
    path            lib/backuptools
    remotes     [
                    origin
                    github
                ]
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
        # find canonical remote
        remotes = filter(lambda r: r.is_canonical, self.remotes.values())
        name = remotes[0].name
        names = self.remotes.keys()
        names = utils.sort_with_elem_as_first(name, names)

        for key in names:
            remote = self.remotes[key]

            urls = remote.urls.keys()
            urls = utils.sort_with_elem_as_first('url', urls)

            for att in urls:
                val = remote.urls[att]
                att = '%s.%s' % (remote.name, att)
                yield att, val
