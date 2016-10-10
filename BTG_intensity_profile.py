#!/usr/bin/env python
from __future__ import division

"""
Extract the voltage from a X line profile based on distance from the
maximum value, which is taken to be the edge of the channel.
"""
from debug_print import pln

import numpy as np

def tabprint(s):
  import sys
  sys.stdout.write('%s\t'%(s))

def compute_line_profile(profile_npz, peak_idx=None):
  from dataloader import DataLoader
  loader = DataLoader(profile_npz)

  zvec = loader.matrix[:, 0]
  voltagevec = loader.matrix[:, 1]

  isfirst = False
  if peak_idx is None:
    peak_idx = np.argmax(voltagevec)
    isfirst = True

  peak_zpos = zvec[peak_idx]
  pln('Peak idx=%d z=%.2f'%(peak_idx, peak_zpos))

  sample_zdist_vec = list(np.arange(0, 59)*20)

  # travel towards zero from peakidx and output a value a soon as the
  # distance exceeds one of the markers set down in sample_zdist_vec
  sample_idx = peak_idx

  samples = list()
  while sample_idx >= 0 and len(sample_zdist_vec) > 0:
    zpos = zvec[sample_idx]
    dist = peak_zpos - zpos
    voltage = voltagevec[sample_idx]

    if dist >= sample_zdist_vec[0]:
      samples.append((dist, voltage))
      sample_zdist_vec.pop(0)
    sample_idx -= 1

  parts = profile_npz.split('-')
  scan_num = int(parts[1])
  time = scan_num * 2

  if isfirst:
    tabprint('time(s)/dist (um)\t')
    for dist in map(lambda x:x[0], samples):
      tabprint('%10.4f\t'%(dist))
    print ''


  tabprint('%18.4f'%(time))
  for voltage in map(lambda x:x[1], samples):
    tabprint('%10.4f'%(voltage))
  print ''
  return peak_idx

def main(profile_npz_files=None):
  peak_idx = compute_line_profile(profile_npz_files[0])
  for profile_npz in profile_npz_files[1:]:
    compute_line_profile(profile_npz, peak_idx)

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Measures growth of deformation over time in XZ scans')
  parser.add_argument('profile_npz_files', nargs='+', type=str, help='Line profiles to compute, expected to be the output of wzextract')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))
