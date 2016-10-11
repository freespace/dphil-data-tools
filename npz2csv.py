#!/usr/bin/env python

"""
This script implements Savitzky-Golay filtering on 1D
scan data
"""

import numpy as np

def main(npzs_to_convert=None, column_headers=None, stdout=None, fmt=None):
  from dataloader import DataLoader
  for npz in npzs_to_convert:
    loader = DataLoader(npz)

    header = '\t'.join(column_headers)

    def tocsv(filename):
      np.savetxt(filename, loader.matrix, delimiter='\t', header=header, fmt=fmt)

    if stdout:
      import StringIO
      out = StringIO.StringIO()
      tocsv(out)
      print out.getvalue()
    else:
      from os.path import splitext, extsep
      csvname = splitext(npz)[0] + extsep + 'csv'
      tocsv(csvname)
      print 'CSV saved to', csvname

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Converts npz data to csv')
  parser.add_argument('-column_headers', type=str, default=[], nargs='+', help='If given will be written as column headers')
  parser.add_argument('-stdout', action='store_true', default=False, help='If given output will be written to stdout')
  parser.add_argument('-fmt', type=str, default='%.18e', help='Specifies the output format ala C printf style')
  parser.add_argument('npzs_to_convert', type=str, nargs='+', help='NPZ file to convert')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))
