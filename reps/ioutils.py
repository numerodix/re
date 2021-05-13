from __future__ import absolute_import

import logging
import subprocess

import ansicolor

logger = logging


try:
    input_func = raw_input
except NameError:
    input_func = input

def maybe_decode(value):
    if type(value) == bytes:
        return value.decode()
    return value


def invoke(cwd, args):
    logger.debug("Invoking: [%s] '%s'" % (cwd, ' '.join(args)))
    popen = subprocess.Popen(args, cwd=cwd,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = popen.communicate()
    out = maybe_decode(out).strip()
    err = maybe_decode(err).strip()
    ret = popen.returncode
    if out:
        lines = out.split('\n')
        for line in lines:
            logger.debug("> %s" % ansicolor.blue(line))
    if ret:
        if not err:
            err = ret
        logger.warn("Returned %s" % (err))
    return ret, out, err


def inform(msg, minor=False, major=False):
    if major:
        ansicolor.write_out(ansicolor.yellow('>>> %s\n' % msg))
    elif minor:
        ansicolor.write_out(ansicolor.cyan('-> %s\n' % msg))
    else:
        ansicolor.write_out(ansicolor.green('> %s\n' % msg))

def suggest(msg, minor=False):
    if minor:
        ansicolor.write_out(ansicolor.magenta('-> %s\n' % msg))
    else:
        ansicolor.write_out(ansicolor.magenta('> %s\n' % msg))

def complain(msg, minor=False):
    if minor:
        ansicolor.write_out(ansicolor.yellow('-> %s\n' % msg))
    else:
        ansicolor.write_out(ansicolor.yellow('> %s\n' % msg))

def prompt(msg, minor=False, default_yes=False):
    if default_yes:
        prompt = '[Yn]'
    else:
        prompt = '[yN]'

    if minor:
        ansicolor.write_out(ansicolor.magenta('-> %s %s ' % (msg, prompt)))
    else:
        ansicolor.write_out(ansicolor.magenta('> %s %s ' % (msg, prompt)))
    inp = input_func()

    if default_yes:
        return False if 'n' in inp else True
    else:
        return True if 'y' in inp else False

def output(msg):
    ansicolor.write_out('%s\n' % msg)
