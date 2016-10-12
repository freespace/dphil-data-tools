#!/usr/bin/env python
from __future__ import division

import numpy as np

import dphil_paths

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def compute(growth_npz, S_C):
  from dataloader import DataLoader

  loader = DataLoader(growth_npz)
  mat = loader.matrix

  # we capture 1 scans extra of information, so ignore it
  tvec = mat[1:, 0]
  if S_C:
    movement_vec = mat[1:, 2]
  else:
    movement_vec = mat[1:, 5]

  d_residual_vec = movement_vec[1:] - movement_vec[:-1]

  TAB='\t'
  from os.path import basename
  d_residual_vec_sorted = np.sort(d_residual_vec)

  print basename(growth_npz), TAB, d_residual_vec_sorted[-1], TAB, d_residual_vec_sorted[0]

def main(growth_npz_vec,  S_C=False):
  for growth_npz in growth_npz_vec:
    compute(growth_npz, S_C)

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Computes the growth derivative in the detrended central region between t=0..50 and t=70..120 minutes')
  parser.add_argument('-S_C', action='store_true', help='If given derivative of S_C is computed instead of e_C')
  parser.add_argument('growth_npz_vec', type=str, nargs='+', help='Growth data file (.npz) with which to compute the growth gradient')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))

