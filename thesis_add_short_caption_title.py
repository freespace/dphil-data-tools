#!/usr/bin/env python
"""
This can only be run ONCE on lyx files b/c it doesn't check
if short-caption already exists!
"""
class Inset(object):
  begin_line=None
  inner_text=None

  def __init__(self, begin_line):
    self.begin_line = begin_line
    self.inner_text = list()

  def append(self, text):
    self.inner_text.append(text)

  def __str__(self):
    s = self.begin_line
    for t in self.inner_text:
      s += '\n\t'+t
    return s

  def short_title(self):
    # get rid of lines starting with \ which are lyx commands
    caption = filter(len, self.inner_text)
    caption = filter(lambda l:not l[0] == '\\', caption)
    caption = ' '.join(caption)

    # if there is a latex label, then there will be something like
    # LatexCommand label name "xxxx" before the rest of the caption.
    # we need to remove this
    if 'LatexCommand label name' in caption:
      caption = caption.split('"', 2)[-1]

    if '.' in caption:
      head, tail = caption.split('.', 1)
      if ',' in head:
        head = head.split(',', 1)[0]
      # remove () since it normally contains things like (a) text and (b) some
      # more text and also b/c I tend to put \um{1} and things like that in it,
      # which this basic parser can't handle, since I would otherwise need to
      # expand certain insets
      in_bracket = False
      shorttitle = ''
      for c in head:
        if c == '(':
          in_bracket = True
        elif c == ')' and in_bracket:
          in_bracket = False
        elif not in_bracket:
          shorttitle += c
      # remove double spaces
      shorttitle = ' '.join(filter(len, shorttitle.split(' ')))
      return shorttitle.strip()
    else:
      return caption

def add_short_captions(lyx_file):
  with open(lyx_file) as f:
    contents = f.read()
  # write a copy as bakup
  lyxbak = lyx_file+'.bak'
  with open(lyxbak, 'w') as f:
    f.write(contents)
    print 'Backup wrote out to', lyxbak

  output = list()
  inset_stack = list()
  for line in contents.split('\n'):
    if line.startswith(r'\begin_inset'):
      inset = Inset(line)
      inset_stack.insert(0, inset)
    elif line.startswith(r'\end_inset'):
      inset = inset_stack.pop(0)
      if len(inset_stack):
        outbuf = inset_stack[0].inner_text
      else:
        outbuf = output

      outbuf.append(inset.begin_line)
      outbuf.extend(inset.inner_text)

      if 'Caption Standard' in inset.begin_line:
        shorttitle = inset.short_title()
        if len(shorttitle):
          extracontent=r"""
          \begin_inset Argument 1
          status open

          \begin_layout Plain Layout
          %s
          \end_layout

          \end_inset
          """%(shorttitle)

          extracontent = map(str.strip, extracontent.split('\n'))
          while not outbuf[-1] == '\\end_layout':
            outbuf.pop()
          outbuf.pop()

          outbuf.extend(extracontent)
          outbuf.append('\\end_layout')

      outbuf.append(line)
    elif len(inset_stack) == 0:
      # we are not in an inset, append to output
      output.append(line)
    else:
      # we are in an inset, so append to the inset
      inset = inset_stack[0]
      inset.append(line)

  output = '\n'.join(output)
  with open(lyx_file, 'w') as f:
    f.write(output)

def main(lyx_files_vec):
  for lyx_file in lyx_files_vec:
    add_short_captions(lyx_file)

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Adds short titles to all captions in a lyx document.')
  parser.add_argument('lyx_files_vec', type=str, nargs='+', help='lyx files to modify')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))

