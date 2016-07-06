#!/usr/bin/env python

def removeprefix(s):
  # For files that already have 'XXXX-', where X are digits, we remove
  # the prefix to avoid producing prefixes like 0001-0002-. This allows us
  # to run the script in a directory with file that were previously renamed.
  prefix = s[:5]

  if filter(str.isdigit, prefix) == prefix[:4] and prefix[-1] == '-':
    return s[5:]
  else:
    return s

def timestampcmp(a, b):
  def getts(s):
    # SIOS will name a file with a minute timestamp at the end
    # w.g. XXXX-YYYY-HHMM.EEEE.TTTT
    #
    # Wjere HHMM is hour and minute. We therefore look for a 4 character pure
    # digit part and assume that is the timestamp
    #
    # We extract the timestamp and return it as an integer
    # handle the extensions by replacing . with -
    s = s.replace('.', '-')
    parts = s.split('-')[::-1]
    for p in parts:
      if len(p) == 4 and p.isdigit():
        return int(p)
    return 99999

  def getscannum(s):
    # SIOS will also add a scan number which we should use for sorting as
    # well. This number can be identified as a string in the form of
    # -XXX- where X are digits, and the number of Xs are variable.
    parts = s.split('-')

    # b/c it must be surrounded by -, it cannot be the first or last part
    parts = parts[1:-1]

    for p in parts:
      if filter(str.isdigit, p) == p and len(p):
        return int(p)

    return 999

  na = getts(a) * 1000 + getscannum(a)
  nb = getts(b) * 1000 + getscannum(b)

  return na - nb

def main(**kwargs):
  filesvec = kwargs['filestorename']
  doit = kwargs['doit']

  # sort by timestamp
  filesvec.sort(cmp=timestampcmp)

  filesvecnoprefix = map(removeprefix, filesvec)

  def f(tt):
    idx,s = tt
    return '%04d-%s'%(idx, s)

  # now append nnnn to each file name base on its position in the array
  newfilesvec = map(f, enumerate(filesvecnoprefix))

  from os import rename
  for oldname, newname in zip(filesvec, newfilesvec):
    print oldname, '--->', newname

    if doit:
      rename(oldname, newname)

  print ''
  if doit:
    print 'Files renamed'
  else:
    print 'Files not renamed. Pass `-doit` to commit to above mapping'

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Renames file by timestamp')

  parser.add_argument('filestorename', nargs='+', help='Files to rename')
  parser.add_argument('-doit', action='store_true', help='Actually rename files, not just print the mapping')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))

