#!/usr/bin/env python
"""
This file operates on all files given via the commandline, and performs the
following:

  - appends or prepends a piece of string
  - deletes the first or the last line of the file

Strings to append or prepend may contain the following special sequences. Upon
encountering these sequences, substitutions are made.

  - @filename: replaced with the name of the file
  - @filenameNoExt: replaced with the name of the file minus the extension

Note that the delete operation will only delete lines that start with #, and
performed BEFORE insertion. e.g. if you delete_first and prepend, you end up
changing the first line.
"""

def operate(**kwargs):
  plotfiles = kwargs['plotfiles']
  append = kwargs['append']
  prepend = kwargs['prepend']
  delete_last = kwargs['delete_last']
  delete_first = kwargs['delete_first']
  force = kwargs['force']

  for plotfile in plotfiles:
    print plotfile
    def sub(s):
      from os.path import splitext
      s = s.replace('@filenameNoExt', splitext(plotfile)[0])
      s = s.replace('@filename', plotfile)
      return s

    with open(plotfile) as pf:
      lines = pf.readlines()

      if delete_last == True:
        if not force:
          assert(lines[-1].startswith('#'))
        lines = lines[:-1]
        print '\tDeleted last line'
      if delete_first == True:
        if not force:
          assert(lines[0].startswith('#'))
        lines = lines[1:]
        print '\tDeleted first line'

      eol = '\n'
      if '\r\n' in lines[0]:
        eol = '\r\n'

      if append is not None:
        for l in append:
          newline = sub(l)
          lines.append(newline+eol)
          print '\tAppended',newline
      if prepend is not None:
        for l in prepend:
          newline = sub(l)
          lines.insert(0, newline+eol)
          print '\tPrepended',newline

    with open(plotfile, 'w') as pf:
      pf.writelines(lines)

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='Edits enmass plotfiles')

  parser.add_argument('plotfiles', type=str, nargs='+', help='Plotfiles to edit')
  parser.add_argument('-append', type=str, nargs=1, help='String to append')
  parser.add_argument('-prepend', type=str, nargs=1, help='String to prepend')
  parser.add_argument('-delete_last', action='store_true', help='Deletes the last line in the file')
  parser.add_argument('-delete_first', action='store_true', help='Deletes the first line in the file')
  parser.add_argument('-force', action='store_true', help='Forces deletions even if a line does not start with a #')

  cmdargs = vars(parser.parse_args())
  operate(**cmdargs)
