reps
====

.. image:: https://badge.fury.io/py/reps.png
        :target: https://badge.fury.io/py/reps

.. image:: https://pypip.in/license/reps/badge.png
        :target: https://pypi.python.org/pypi/reps/


Quickstart
----------

.. code:: bash

    $ pip install reps
    $ re


Usage
-----

Detecting your repositories
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Usage of ``re`` is centered around the contents of ``.reconfig`` in the
current working directory. To generate a ``.reconfig`` from some repositories
you have at hand...

.. code:: bash

    $ re list
    [ansicolor:git]
        origin.url = https://github.com/numerodix/ansicolor
    [ejabberd:git]
        origin.url = https://github.com/processone/ejabberd.git
    [xmonad:git]
        origin.url = https://github.com/xmonad/xmonad
    > Run with -u to update .reconfig


Re-run with ``-u`` to write the detected config to ``.reconfig``.


Updating repositories
^^^^^^^^^^^^^^^^^^^^^

The most common use case for ``re`` is simply syncing your repos.

.. code:: bash

    $ re pull
    > Fetching ansicolor
    > Fetching ejabberd
    > Fetching xmonad
    > Merging ansicolor
    -> Setting up local tracking branch develop
    > Merging ejabberd
    -> Setting up local tracking branch 1.1.x
    -> Setting up local tracking branch 2.1.x
    -> Setting up local tracking branch obsolete_3alpha
    -> Setting up local tracking branch 2.0.x
    > Merging xmonad

``re`` simply runs git in the background. Fetching and merging are done
in separate steps. During merging git may prompt you to resolve merge
conflicts, so by fetching all the repos first we can do away with all
the network io first and avoid interleaving that with interactive
use of git.
