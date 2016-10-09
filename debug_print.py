#!/usr/bin/env python

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def debug(*args, **kwargs):
  import sys
  sys.stderr.write(bcolors.WARNING)
  for s in args:
    sys.stderr.write(str(s))
    sys.stderr.write(' ')
  sys.stderr.write(bcolors.ENDC)

  if kwargs.get('newline', False):
    sys.stderr.write('\n')

def p(*args):
  debug(*args)

def pln(*args):
  debug(*args, newline=True)
