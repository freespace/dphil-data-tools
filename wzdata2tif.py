#!/usr/bin/env python
"""
This script converts WZ data to 16 bit gray scale tif images. W is an axis
orthogonal to Z, e.g. X or Y

The script performs certain adjustments to make the output compatible with fluorescence microscope images:

  - The Z axis is scaled by 1.33 to account for refractive index of water and
    the resulting magnification of motion in air.
  - The image is made square by scaling the image in width or height as
    needed. This transformation preserved the smaller of pixel height or width before scaling
  - If the image is an YZ image, the image is inverted vertically to place the
    origin at bottom-left as expected.

In images produced by this program, the Z position *always* increases as one moves left-to-right.
"""
from __future__ import division
# we will need YZScanData from SIOS. Should fix this at some point
SIOS_PATH='../code/SIOS_control;../../code/SIOS_control'

# we will also need the stats module from data analysis tools
DATA_TOOLS_PATH='.'

import sys
sys.path = SIOS_PATH.split(';') + sys.path
sys.path.insert(0, DATA_TOOLS_PATH)

import matplotlib
matplotlib.use('Qt4Agg')

import matplotlib.pyplot as plt
import numpy as np

def main(**kwargs):
  noadjust = kwargs['noadjust']
  datafile = kwargs['datafile']
  npzfile = np.load(datafile)
  scandata = npzfile['scandata'].item()

  pix = scandata.matrix

  zvec = scandata.zpositionvec
  # correct for the fact these scans are taken in water, where the focus
  # travels 1.33 mm for every 1 mm the objective travels in air
  z0 = zvec[0]
  zvec -= z0
  zvec *= 1.33
  zvec += z0

  wvec = scandata.wpositionvec

  wrange = wvec.max() - wvec.min()
  zrange = zvec.max() - zvec.min()

  pw = zrange/(len(zvec)-1)
  ph = wrange/(len(wvec)-1)

  # pix is in volts (0..20) and we want to convert it to uint16 as follows:
  # n = (2**16-1)*v/20
  # Where n is the integer result, v is the voltage we have stored.

  intpix = (2**16-1)*pix/20
  intpix = intpix.astype(np.uint16)

  h,w = intpix.shape

  from PIL import Image
  im = Image.fromstring('I;16', (w, h), intpix.tostring())

  if not noadjust:
    newsize = None
    if pw > ph:
      # pixel width is larger than pixel height, we need to make the image
      # have more pixels in X axis to reduce the pixel width when holding
      # the physical size of the image constant
      newsize = (w * pw/ph, h)
      pw /= pw/ph
    elif ph > pw:
      # similarly when pixels are taller than they are wide, we need to add
      # more pixels in the Y direction while holding the physical size of
      # the image constant to reduce the pixel height
      newsize = (w, h*ph/pw)
      ph /= ph/pw
  
    if newsize is not None:
      adjusted = True
      im = im.resize(map(int,newsize), Image.NEAREST)

  print 'Image width=%.2f um, height=%.2f um'%(zrange+pw, wrange)
  print '  pixel width=%.2f um, height=%.2f um, adjusted=%s'%(pw, ph, not noadjust)
  if noadjust:
    print '  pixel aspect ratio=%.2f (h:w=%.2f)'%(pw/ph, ph/pw)

  if scandata.w == 'Y':
    print '  YZ scan detected, inverting image vertically'
    im = im.transpose(Image.FLIP_TOP_BOTTOM)

  from os.path import splitext, extsep
  name,ext = splitext(datafile)
  outfile = name + extsep + 'tif'
  im.save(outfile)
  print ''
  print 'TIFF written to', outfile

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='GNUplot replacement plotter')

  parser.add_argument('-noadjust', 
                      action='store_true',
                      help='No adjustments are made to the image after converting from matrix.')
  parser.add_argument('datafile', help='YZ data file')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))