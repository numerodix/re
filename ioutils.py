import logging
import subprocess

from lib import ansicolor

log = logging

def invoke(cwd, args):
    log.debug("Invoking: [%s] '%s'" % (cwd, ' '.join(args)))
    popen = subprocess.Popen(args, cwd=cwd,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = popen.communicate()
    out = str(out).strip()
    err = str(err).strip()
    ret = popen.returncode
    if ret:
        if not err:
            err = ret
        log.warn("[%s] '%s' returned %s" % (cwd, ' '.join(args), err))
    return ret, out, err


def inform(msg, minor=False):
    if minor:
        ansicolor.write_out(ansicolor.cyan('-> %s\n' % msg))
    else:
        ansicolor.write_out(ansicolor.green('> %s\n' % msg))

def suggest(msg):
    ansicolor.write_out(ansicolor.cyan('> %s\n' % msg))

def complain(msg):
    ansicolor.write_out(ansicolor.yellow('> %s\n' % msg))


def output(msg):
    ansicolor.write_out('%s\n' % msg)
