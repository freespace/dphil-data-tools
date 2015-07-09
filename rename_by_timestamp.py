#!/usr/bin/env python

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
    return None

  return getts(a) - getts(b)

def main(**kwargs):
  filesvec = kwargs['filestorename']
  
  # sort by timestamp
  filesvec.sort(cmp=timestampcmp)

  def f(tt):
    idx,s = tt
    return '%04d-%s'%(idx, s)

  # now append nnnn to each file name base on its position in the array
  newfilesvec = map(f, enumerate(filesvec))

  from os import rename
  for oldname, newname in zip(filesvec, newfilesvec):
    print oldname, '--->', newname
    rename(oldname, newname)

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Renames file by timestamp')

  parser.add_argument('filestorename', nargs='+', help='Files to rename')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))

