#!/usr/bin/env python

def parse_plotfile(plotfilename):
  """
  Returns a list of csvfiles found in a plotfile, and any command line
  arguments as a list suitable for parsing to ArgumentParser.
  """
  import shlex
  csvfiles = []
  cmdline = ''
  with open(plotfilename) as pf:
    for line in pf.readlines():
      line = line.strip()
      if line.startswith('#!'):
        line = line[2:]
        cmdline += line
        cmdline += ' '
      elif not line.startswith('#'):
        if len(line):
          if ':' in line:
            # this allows pasting of grep output directly, as long as there
            # is no other ':'
            line = line.split(':')[0]
          csvfiles.append(line)

  return csvfiles, shlex.split(cmdline)
