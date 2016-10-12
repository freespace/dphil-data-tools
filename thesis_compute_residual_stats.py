#!/usr/bin/env python
from __future__ import division

import numpy as np

import dphil_paths
from debug_print import bcolors

def compute(growth_npz, debug):
  from dataloader import DataLoader

  loader = DataLoader(growth_npz)
  mat = loader.matrix

  # we capture 1 scans extra of information, so ignore it
  tvec = mat[:-1, 0]
  residual_vec = mat[:-1, 5]

  dt = (tvec[2]-tvec[0])/2

  US_exp_window = 10 * 60 // dt

  n = (residual_vec.size - US_exp_window) // 2

  residual_vec_pre_US = residual_vec[:n]
  residual_vec_post_US = residual_vec[-n:]

  u0 = np.mean(residual_vec_pre_US)
  sd0 = np.std(residual_vec_pre_US)

  u1 = np.mean(residual_vec_post_US)
  sd1 = np.std(residual_vec_post_US)

  print growth_npz
  print '\tMean residual up to',(tvec[n-1] - tvec[0])/60, 'min'
  print bcolors.OKGREEN + '\t\t%.2f'%(u0), '\tSD %.2f'%(sd0), bcolors.ENDC


  print '\tMean residual from',(tvec[-n] - tvec[0])/60, 'min'
  print bcolors.OKGREEN + '\t\t%.2f'%(u1), '\tSD %.2f'%(sd1), bcolors.ENDC

  print '\tu_1 - u_0'
  # http://stattrek.com/sampling/difference-in-means.aspx?tutorial=ap
  # http://onlinestatbook.com/2/sampling_distributions/samplingdist_diff_means.html
  # Note that the result is the standard error of the mean, which is the
  # standard deviation in difference of mean
  sd_diff = (sd0**2/residual_vec_pre_US.size + sd1**2/residual_vec_post_US.size)**0.5
  print bcolors.WARNING + '\t\t%.2f'%(u1-u0), '\tSEM=%.2f'%(sd_diff), bcolors.ENDC

  import scipy.stats as stats
  print '\tDependent t-test'
  t, p = stats.ttest_rel(residual_vec_pre_US, residual_vec_post_US)
  print '\t\t'+bcolors.FAIL, 't=%.2f, p=%.4f'%(t, p), bcolors.ENDC

  if debug:
    import matplotlib.pyplot as plt
    import matplotlib_setup
    from utils import keypress

    plt.plot(residual_vec_pre_US, label='pre')
    plt.hold(True)
    plt.plot(residual_vec_post_US, label='post')
    plt.legend()

    plt.gcf().canvas.mpl_connect('key_press_event', keypress)

    plt.show()
    plt.close()

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

