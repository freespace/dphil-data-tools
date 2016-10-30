#!/usr/bin/env python
from __future__ import division

import numpy as np

import dphil_paths
from debug_print import pln

"""
Plots a PAM image from .mat files from Ersi
"""

def main(mat_file=None, pdf=False, match_SIOS=False, png=False, 
         cbar=False, vmin=None, vmax=None, get_stats=False, title=None,
         log_norm=False, square_px=False):
  from scipy.io import loadmat
  mat = loadmat(mat_file, struct_as_record=False, squeeze_me=True)
  PAM_map = mat['imgRcb1']

  if get_stats:
    vmin = PAM_map.min()
    vmax = PAM_map.max()
    area_integral = np.sum(PAM_map)

    def tprint(*args):
      args = map(str, args)
      print '\t'.join(args)

    tprint(mat_file, vmin, vmax, area_integral)
    return 0

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

  if log_norm:
    from matplotlib.colors import LogNorm
    if vmin is None:
      vmin = PAM_map.min()
    if vmax is None:
      vmax = PAM_map.max()

    norm = LogNorm(vmin=vmin, vmax=vmax)
  else:
    norm = None

  if square_px:
    aspect = px_w/px_h
  else:
    aspect = None

  import matplotlib_setup
  ax = plt.gca()
  im = ax.imshow(PAM_map,
                 interpolation='None',
                 extent=[left, right, bottom, top],
                 origin='upper',
                 aspect=aspect,
                 vmin=vmin,
                 vmax=vmax,
                 norm=norm)


  if cbar:
    cbar = plt.colorbar(im, shrink=0.3, pad=0.04, aspect=10)

  if title is not None:
    plt.title(title)

  if pdf or png:
    from os.path import basename
    mat_file = basename(mat_file)
    if pdf:
      pdfname = mat_file+'.pdf'
      fig = plt.gcf()
      fig.savefig(pdfname, bbox_inches='tight')
      pln('PDF saved to %s'%(pdfname))

    if png:
      pngname = mat_file+'.png'
      fig = plt.gcf()
      fig.savefig(pngname, bbox_inches='tight')
      pln('png saved to %s'%(pngname))

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
  parser.add_argument('-png', action='store_true', help='If given plot is saved as a png')
  parser.add_argument('-cbar', action='store_true', help='If given colorbar will be plotted')
  parser.add_argument('-vmin', type=float, default=None, help='Specifies the lower bound pixel value')
  parser.add_argument('-vmax', type=float, default=None, help='Specifies the upper bound pixel value')
  parser.add_argument('-title', type=str, default=None, help='Sets the title of the plot')
  parser.add_argument('-log_norm', action='store_true', default=False, help='Sets the title of the plot')
  parser.add_argument('-get_stats', action='store_true', help='Gets vmim, vmax and other stats without plotting anything')
  parser.add_argument('-match_SIOS', action='store_true', help='If given image is transformed so it can be overlaid on SIOS images')
  parser.add_argument('-square_px', action='store_true', help='If given plot will be scaled to pixels are square. This will distort features as pixels are intrinsically non-square')
  parser.add_argument('mat_file', help='Matlab fig files')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))

