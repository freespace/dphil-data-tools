#!/usr/bin/env python
from __future__ import division

import numpy as np

import dphil_paths

def compute(growth_npz, debug):
  from dataloader import DataLoader

  loader = DataLoader(growth_npz)
  mat = loader.matrix

  # we capture 1 scans extra of information, so ignore it
  tvec = mat[:-1, 0]
  movement_vec = mat[:-1, 5]

  d_movement_vec = movement_vec[1:] - movement_vec[:-1]
  
  dt = (tvec[2]-tvec[0])/2

  US_exp_window = 10 * 60 // dt

  n = (d_movement_vec.size - US_exp_window) // 2

  d_movement_vec_pre_US = d_movement_vec[:n]
  d_movement_vec_post_US = d_movement_vec[-n:]

  print growth_npz
  print '\tMean gradient up to',(tvec[n-1] - tvec[0])/60, 'min'
  print '\t\t',np.mean(d_movement_vec_pre_US), 'SD', np.std(d_movement_vec_pre_US)


  print '\tMean gradient from',(tvec[-n] - tvec[0])/60, 'min'
  print '\t\t',np.mean(d_movement_vec_post_US), 'SD', np.std(d_movement_vec_post_US)

  if debug:
    import matplotlib.pyplot as plt
    import matplotlib_setup
    from utils import keypress

    plt.plot(d_movement_vec_pre_US)
    plt.hold(True)
    plt.plot(d_movement_vec_post_US)

    plt.gcf().canvas.mpl_connect('key_press_event', keypress)

    plt.show()
    plt.close()

  from scipy.stats import ttest_rel

  t, prob = ttest_rel(d_movement_vec_pre_US, d_movement_vec_post_US)
  print '\tt=',t,'p=',prob


def main(growth_npz_vec, debug=False):
  for growth_npz in growth_npz_vec:
    compute(growth_npz, debug)

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Computes the growth derivative in the detrended central region between t=0..50 and t=70..120 minutes')
  parser.add_argument('-debug', action='store_true', help='If given the sections boundaries will be shown for each image.')
  parser.add_argument('growth_npz_vec', type=str, nargs='+', help='Growth data file (.npz) with which to compute the growth gradient')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))

