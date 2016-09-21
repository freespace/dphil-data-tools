#!/usr/bin/env python

"""
This script implements Savitzky-Golay filtering on 1D
scan data
"""

import numpy as np

def main(npzs_to_convert=None, column_headers=None):
  from dataloader import DataLoader
  for npz in npzs_to_convert:
    loader = DataLoader(npz)

    from os.path import splitext, extsep
    csvname = splitext(npz)[0] + extsep + 'csv'
    header = '\t'.join(column_headers)
    np.savetxt(csvname, loader.matrix, delimiter='\t', header=header)
    print 'CSV saved to', csvname

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Converts npz data to csv')
  parser.add_argument('-column_headers', type=str, default=[], nargs='+', help='If given will be written as column headers')
  parser.add_argument('npzs_to_convert', type=str, nargs='+', help='NPZ file to convert')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))
