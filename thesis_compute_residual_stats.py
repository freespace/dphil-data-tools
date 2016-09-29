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

def compute(growth_npz, debug):
  from dataloader import DataLoader

  loader = DataLoader(growth_npz)
  mat = loader.matrix

  # we capture 1 scans extra of information, so ignore it
  tvec = mat[:-1, 0]
  movement_vec = mat[:-1, 5]

  dt = (tvec[2]-tvec[0])/2

  US_exp_window = 10 * 60 // dt

  n = (movement_vec.size - US_exp_window) // 2

  movement_vec_pre_US = movement_vec[:n]
  movement_vec_post_US = movement_vec[-n:]

  u0 = np.mean(movement_vec_pre_US)
  sd0 = np.std(movement_vec_pre_US)

  u1 = np.mean(movement_vec_post_US)
  sd1 = np.std(movement_vec_post_US)

  print growth_npz
  print '\tMean residual up to',(tvec[n-1] - tvec[0])/60, 'min'
  print bcolors.OKGREEN + '\t\t%.2f'%(u0), '\tSD %.2f'%(sd0), bcolors.ENDC


  print '\tMean residual from',(tvec[-n] - tvec[0])/60, 'min'
  print bcolors.OKGREEN + '\t\t%.2f'%(u1), '\tSD %.2f'%(sd1), bcolors.ENDC

  if debug:
    import matplotlib.pyplot as plt
    import matplotlib_setup
    from utils import keypress

    plt.plot(movement_vec_pre_US)
    plt.hold(True)
    plt.plot(movement_vec_post_US)

    plt.gcf().canvas.mpl_connect('key_press_event', keypress)

    plt.show()
    plt.close()

  #from scipy.stats import ttest_rel
  #
  #t, prob = ttest_rel(d_movement_vec_pre_US, d_movement_vec_post_US)
  #
  #print bcolors.OKGREEN,'\tt=',t, 'df=', d_movement_vec_post_US.size - 1, 'p=',prob, bcolors.ENDC


def main(growth_npz_vec, debug=False):
  for growth_npz in growth_npz_vec:
    compute(growth_npz, debug)

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Computes statistics of the central-centre fluorescence front displacement residual between t=0..50 and t=70..120 minutes')
  parser.add_argument('-debug', action='store_true', help='If given the sections boundaries will be shown for each image.')
  parser.add_argument('growth_npz_vec', type=str, nargs='+', help='Growth data file (.npz) with which to compute the growth gradient')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))

