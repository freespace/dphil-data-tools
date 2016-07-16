#!/usr/bin/env python
from __future__ import division

"""
Computes the sum of PMT values over the entire image.
"""

import dphil_paths

def main(**kwargs):
  datafiles = kwargs['datafiles']

  cols = ["Source Filename", "Total PMT Value", "# Pixels", "Pixel PMT Density"]
  print '\t'.join(cols)

  for datafile in datafiles:
    pixsum, npix = get_sum(datafile)
    print "%s\t%f\t%d\t%f"%(datafile, pixsum, npix, pixsum/npix)

def get_sum(datafile):
  import numpy as np
  npzfile = np.load(datafile)
  scandata = npzfile['scandata'].item()

  if scandata.w is None:
    print datafile + ' does not define w axis, not processing.'
    return None

  return np.sum(scandata.matrix), scandata.matrix.size

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Computes the sum of PMT values over the entire image')
  parser.add_argument('datafiles', nargs='+', help='WZ data files')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))
