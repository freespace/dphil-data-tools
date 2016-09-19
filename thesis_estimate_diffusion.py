#!/usr/bin/env python
from __future__ import division

import numpy as np

import dphil_paths

def main(growth_files=None):
  from dataloader import DataLoader

  # units of um/min
  diffusion_speed_est_vec = list()
  for npzfile in growth_files:
    loader = DataLoader(npzfile)
    mat = loader.matrix

    tvec = mat[:, 0]
    sec1 = mat[:, 1]
    dz = sec1[-1]

    # remember we want rate in um/min
    dt = (tvec[-1] - tvec[0])/60
    diffusion_speed_est_vec.append(dz/dt)

  diffusion_speed_mean = np.mean(diffusion_speed_est_vec)
  diffusion_speed_sd = np.std(diffusion_speed_est_vec)

  print 'Estimated diffusion speed: %.2f um/min SD %.2f um/min'%(diffusion_speed_mean, diffusion_speed_sd)

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Estimates diffusion speed in um/min using data produced by wzgrowth.py')
  parser.add_argument('growth_files', nargs='+', type=str, help='Growth data files (.npz) from which to extract diffusion distance')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))
