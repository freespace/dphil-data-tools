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

  d_residual_vec = movement_vec[1:] - movement_vec[:-1]

  dt = (tvec[2]-tvec[0])/2

  US_exp_window = 10 * 60 // dt

  n = (d_residual_vec.size - US_exp_window) // 2

  d_residual_vec_pre_US = d_residual_vec[:n]
  d_residual_vec_post_US = d_residual_vec[-n:]

  def mean_std(x):
    return np.mean(x), np.std(x)
  u_d0, sd0 = mean_std(d_residual_vec_pre_US)
  u_d1, sd1 = mean_std(d_residual_vec_post_US)

  print growth_npz
  print '\tMean gradient up to',(tvec[n-1] - tvec[0])/60, 'min'
  print bcolors.OKGREEN + '\t\t%.2f'%(u_d0), 'SD %.2f'%(sd0), bcolors.ENDC


  print '\tMean gradient from',(tvec[-n] - tvec[0])/60, 'min'
  print bcolors.OKGREEN + '\t\t%.2f'%(u_d1), 'SD %.2f'%(sd1), bcolors.ENDC

  print '\tu_1 - u_0'
  # http://stattrek.com/sampling/difference-in-means.aspx?tutorial=ap
  sd_diff = (sd0**2/d_residual_vec_pre_US.size + sd1**2/d_residual_vec_post_US.size)**0.5
  print bcolors.WARNING + '\t\t%.2f'%(u_d1-u_d0), '\tSD=%.2f'%(sd_diff), bcolors.ENDC

  import scipy.stats as stats
  print '\tDependent t-test'
  t, p = stats.ttest_rel(d_residual_vec_pre_US, d_residual_vec_post_US)
  print '\t\t'+bcolors.FAIL, 't=%.2f, p=%.4f'%(t, p), bcolors.ENDC

  if debug:
    import matplotlib.pyplot as plt
    import matplotlib_setup
    from utils import keypress

    plt.plot(d_residual_vec_pre_US)
    plt.hold(True)
    plt.plot(d_residual_vec_post_US)

    plt.gcf().canvas.mpl_connect('key_press_event', keypress)

    plt.show()
    plt.close()

  #from scipy.stats import ttest_rel
  #
  #t, prob = ttest_rel(d_residual_vec_pre_US, d_residual_vec_post_US)
  #
  #print bcolors.OKGREEN,'\tt=',t, 'df=', d_residual_vec_post_US.size - 1, 'p=',prob, bcolors.ENDC


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

