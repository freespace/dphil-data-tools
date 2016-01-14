#!/usr/bin/env python
"""
This script converts WZ data to 16 bit gray scale tif images. W is an axis
orthogonal to Z, e.g. X or Y

The script performs certain adjustments to make the output compatible with fluorescence microscope images:

  - The Z axis is scaled by 1.33 to account for refractive index of water and
    the resulting magnification of motion in air.
  - The image is made square by scaling the image vertically so pixel height
    matches pixel width. We do not scale by width because scans in Z tend to be
    fixed while scans in X/Y are not. Preserving the width allows for easier
    comparisons.
  - If the image is an YZ image, the image is inverted vertically to place the
    origin at bottom-left as expected.

In images produced by this program, the Z position *always* increases as one moves left-to-right.
"""
from __future__ import division
import os
# we will need YZScanData from SIOS. Should fix this at some point
homedir = os.path.expanduser('~')
SIOS_PATH=['/data/DPhil/code/SIOS_control',
            os.path.join(homedir, 'DPhil', 'code', 'SIOS_control')]

import sys
sys.path = SIOS_PATH + sys.path

import matplotlib
matplotlib.use('Qt4Agg')

import matplotlib.pyplot as plt
import numpy as np

def convert(datafile, noadjust):
  npzfile = np.load(datafile)
  scandata = npzfile['scandata'].item()

  if scandata.w is None:
    print datafile + ' does not define w axis, not processing.'
    return None

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

  # assumption is that all z scans are done using the same z stepping
  pw = zrange/(len(zvec))
  ph = wrange/(len(wvec))

  # the scan matrix stores voltage values as floats. The original values were
  # unsigned 16 bit integers. We undo the transformation, which is somewhat
  # terrible, using
  #   n = (2**16-1)*v/20
  # Where n is the integer result, v is the voltage we have stored.
  #
  # Note that while the ADS7825 uses 16 bit integers to hold +/-10 V, due to
  # the way we sum multiple readings to implement exposure control, we in fact
  # treat all integers as unsigned and add them together.
  pix = scandata.matrix

  intpix = (2**16-1)*pix/20
  intpix = intpix.astype(np.uint16)

  h,w = intpix.shape

  from PIL import Image
  im = Image.fromstring('I;16', (w, h), intpix.tostring())

  if not noadjust:
    newsize = None
    if int(ph*100) != int(pw*100):
      # make pixels square. This means scaling the image in height until
      # ph matches pw.
      newsize = (w, h*ph/pw)
      ph /= ph/pw

    if newsize is not None:
      adjusted = True
      im = im.resize(map(int,newsize), Image.NEAREST)

  print 'Image width=%.2f um, height=%.2f um'%(zrange, wrange)
  print '  pixel width=%.2f um, height=%.2f um, adjusted=%s'%(pw, ph, not noadjust)
  if noadjust:
    print '  pixel aspect ratio=%.2f (h:w=%.2f)'%(pw/ph, ph/pw)

  if scandata.w == 'Y':
    print '  YZ scan detected, inverting image vertically'
    im = im.transpose(Image.FLIP_TOP_BOTTOM)

  # construct some metadata to save with the image
  zlim = (zvec[0], zvec[-1])
  wlim = (wvec[0], wvec[-1])

  from time import ctime
  tstart = scandata.zscandatavec[0][1].starttime
  tend = scandata.zscandatavec[-1][1].endtime
  metadata = dict(width=zrange,
                  height=wrange,
                  w=scandata.w,
                  pixelwidth=pw,
                  pixelheight=pw,
                  instrument='SIOS',
                  original=datafile,
                  zlim=zlim,
                  wlim=wlim,
                  starttime=ctime(tstart),
                  endtime=ctime(tend),
                  wstep=wvec[1]-wvec[0],
                  adjusted=not noadjust,
                  comments=scandata.comments)

  from os.path import splitext, extsep
  name,ext = splitext(datafile)
  outfile = name + extsep + 'tif'

  from tifffile import imsave
  def tojson(obj):
    from json import dumps
    return dumps(obj, sort_keys=True, indent=2, separators=(',', ': '))

  imsave(outfile,
         np.asarray(im),
         description=tojson(metadata),
         resolution=(10*1000/pw, 10*1000/ph),
         # 296 is the resolution_unit tag. This sets the resolution unit to cm
         # (3) from the default of inch (2)
         extratags=[(296, 'H', 1, 3)])

  print ''
  print 'TIFF written to', outfile

def main(**kwargs):
  noadjust = kwargs['noadjust']
  datafiles = kwargs['datafiles']

  for datafile in datafiles:
    convert(datafile, noadjust)

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Converts 2D SIOS scans to TIFF images')

  parser.add_argument('-noadjust',
                      action='store_true',
                      help='No adjustments are made to the image after converting from matrix.')
  parser.add_argument('datafiles', nargs='+', help='WZ data files')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))
