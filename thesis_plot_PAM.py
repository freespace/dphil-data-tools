#!/usr/bin/env python
from __future__ import division

import numpy as np

import dphil_paths
from debug_print import pln

"""
Plots a PAM image from .mat files from Ersi
"""

def main(mat_file=None, pdf=False, match_SIOS=False):
  from scipy.io import loadmat
  mat = loadmat(mat_file, struct_as_record=False, squeeze_me=True)
  PAM_map = mat['imgRcb1']

  # convert xcoords to mm
  xcoords = mat['xx1']*1000
  ycoords = mat['yy1']*1000

  px_w = np.abs(xcoords[1] - xcoords[0])
  px_h = np.abs(ycoords[1] - ycoords[0])
  pln('Pixel size: w=%f h=%f mm'%(px_w, px_h))

  left = xcoords.min()
  right = xcoords.max()
  top = ycoords.min()
  bottom = ycoords.max()

  import matplotlib.pyplot as plt
  from utils import keypress

  if match_SIOS:
    # b/c the probe pointing into SIOS, its coordinate system along
    # Z increases towards objective. So we need to flip the matrix
    # along its long axis, i.e. columns
    PAM_map = np.fliplr(PAM_map)
    left, right = right, left

    # we don't need to flip the y axis b/c flow is in the direction
    # if increasing Y values, which matches the orientation in SIOS
    # images
    pln('Not adjusting Y b/c flow is already in direction of increasing Y values')

  import matplotlib_setup
  ax = plt.gca()
  im = ax.imshow(PAM_map,
                 interpolation='None',
                 extent=[left, right, bottom, top],
                 origin='upper',
                 aspect=px_w/px_h)

  plt.colorbar(im, shrink=0.3, pad=0.04, aspect=10)

  if pdf:
    pdfname = mat_file+'.pdf'
    fig = plt.gcf()
    fig.savefig(pdfname, bbox_inches='tight')
    pln('PDF saved to %s'%(pdfname))
  else:
    plt.gcf().canvas.mpl_connect('key_press_event', keypress)
    plt.show()
    plt.close()

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Plots PAM images')

  parser.add_argument('-pdf', action='store_true', help='If given plot is saved as a pdf')
  parser.add_argument('-match_SIOS', action='store_true', help='If given image is transformed so it can be overlaid on SIOS images')
  parser.add_argument('mat_file', help='Matlab fig files')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))

