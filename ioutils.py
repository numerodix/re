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
    if out:
        lines = out.split('\n')
        for line in lines:
            log.debug("> %s" % ansicolor.blue(line))
    if ret:
        if not err:
            err = ret
        log.warn("Returned %s" % (err))
    return ret, out, err


def inform(msg, minor=False):
    if minor:
        ansicolor.write_out(ansicolor.cyan('-> %s\n' % msg))
    else:
        ansicolor.write_out(ansicolor.green('> %s\n' % msg))

def suggest(msg):
    ansicolor.write_out(ansicolor.magenta('> %s\n' % msg))

def complain(msg):
    ansicolor.write_out(ansicolor.yellow('> %s\n' % msg))

def prompt(msg, default_yes=False):
    if default_yes:
        prompt = '[Yn]'
    else:
        prompt = '[yN]'
    ansicolor.write_out(ansicolor.magenta('> %s %s ' % (msg, prompt)))
    inp = raw_input()
    if default_yes:
        return False if 'n' in inp else True
    else:
        return True if 'y' in inp else False

def output(msg):
    ansicolor.write_out('%s\n' % msg)
