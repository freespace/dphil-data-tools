#!/usr/bin/env python

"""
This script organises a file full of SIOS scan files into directories
based on the phantom ID.
"""

import os

npz_vec = filter(lambda x:x.endswith('npz'), os.listdir('.'))


def get_phantom_id(filename):
  parts = filename.split('-')
  if len(parts) > 3:
    return parts[3]
  else:
    return None

def get_LUT(filename):
  return os.path.splitext(filename.split('-')[-1])[0]

def dir_LUT(lut):
  return lut

def dir_phantom_id(phantom_id):
  return 'id-'+phantom_id

func_table = dict(by_phantom_id=[get_phantom_id, dir_phantom_id],
                      by_lut=[get_LUT, dir_LUT])
def main(files_to_organise, **kwargs):
  # key identifies which part of the file we should by, e.g. phantom ID
  key_set = set()

  sort_by = filter(lambda x:x[1] if x[0].startswith('by_') else False, kwargs.items())[0][0]
  key_func, dir_func = func_table[sort_by]
  for fname in files_to_organise:
    key_set.add(key_func(os.path.basename(fname)))

  key_set = filter(lambda x:x, list(key_set))
  print 'Got keys', key_set

  for key in key_set:
    print 'Organising key '+key

  # create a dir if needed
    dirname = dir_func(key)+kwargs.get('dir_suffix')
    if os.path.exists(dirname):
      assert os.path.isdir(dirname)
      print '\tdir exists'
    else:
      os.mkdir(dirname)
      print '\tdir created'

    import shutil
    for fname in files_to_organise:
      if key_func(os.path.basename(fname)) == key:
        dst = os.path.join(dirname, fname)
        shutil.move(fname, dst)
        print '\tmoved %s to %s'%(fname, dst)

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Organises files produced in my data processing pipeline')
  parser.add_argument('files_to_organise', type=str, nargs='+', help='Files to organise')
  parser.add_argument('-dir_suffix', type=str, default='', help='If given will be appended to generated directory names')

  g = parser.add_mutually_exclusive_group(required=True)
  g.add_argument('-by_phantom_id', action='store_true', help='Organises by phantom ID')
  g.add_argument('-by_lut', action='store_true', help='Organises by look-up-table')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))
