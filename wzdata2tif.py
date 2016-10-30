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

import numpy as np

import dphil_paths

def convert(datafile, non_square_pixel=False, row_step=1, not_in_water=False):
  npzfile = np.load(datafile)
  scandata = npzfile['scandata'].item()

  if scandata.w is None:
    print datafile + ' does not define w axis, not processing.'
    return None

  zvec = scandata.zpositionvec_raw
  # correct for the fact these scans are taken in water, where the focus
  # travels 1.33 mm for every 1 mm the objective travels in air
  if not not_in_water:
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

  if row_step > 1:
    pix = np.delete(pix, list(range(0, pix.shape[0], row_step)), axis=0)

    # have to update wvec and pixel height as well
    wvec = np.delete(wvec, list(range(0, wvec.shape[0], row_step)), axis=0)
    ph = wrange/(len(wvec))

  intpix = (2**16-1)*pix/20
  intpix = intpix.astype(np.uint16)

  h,w = intpix.shape

  from PIL import Image
  im = Image.fromstring('I;16', (w, h), intpix.tostring())

  if not non_square_pixel:
    # XXX One of the things we need to do is account for the fact that our
    # pixels out of SIOS can be non-square, e.g. 20 um in Z and 50 um in X.
    # Since images are displayed with square pixels, this means that without
    # correction features will appear squashed, for example X, because each
    # pixel represents 50 um, but is shown at the same physical size as the
    # stepping in Z at 20 um.
    #
    # To fix this, we need to simply stretch the image in height, since it is
    # nearly almost the case that Z stepping is going to be the smaller of the
    # two, and Z goes horizontally. The amount we need to stretch by is the
    # ratio between pixel height and pixel width
    #
    # Due to non-integer ratios of pixel height and pixel width, there will be
    # some artifacts. For example, a 20x50 pixel cannot be exactly split into
    # 1x2 array of 20x20 pixels. How this is handled depends on the sampling
    # algorithm as ask PIL to use. For now we are using NEAREST which avoids
    # introducing any "new" data, but does mean we might drop pixels.
    newsize = None
    if int(ph*100) != int(pw*100):
      newsize = (w, h*ph/pw)
      ph /= ph/pw

    if newsize is not None:
      adjusted = True
      im = im.resize(map(int,newsize), Image.NEAREST)

  print 'Image width=%.2f um, height=%.2f um'%(zrange, wrange)
  print '  pixel width=%.2f um, height=%.2f um'%(pw, ph)
  print '  non_square_pixel=%s not_in_water=%s'%(non_square_pixel, not_in_water)

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
                  square_pixel=not non_square_pixel,
                  in_water=not not_in_water,
                  comments=scandata.comments)

  from os.path import splitext, extsep, basename
  name, ext = splitext(datafile)
  outfile = basename(name) + extsep + 'tif'

  def tojson(obj):
    from json import dumps
    return dumps(obj, sort_keys=True, indent=2, separators=(',', ': '))

  imarray = np.asarray(im.getdata(), np.uint16)
  imarray = np.reshape(imarray, (im.size[1], im.size[0], 1))

  assert imarray.shape[:2] == im.size[::-1]

  from tifffile import imsave
  imsave(outfile,
         imarray,
         description=tojson(metadata),
         resolution=(10*1000/pw, 10*1000/ph),
         # 296 is the resolution_unit tag. This sets the resolution unit to cm
         # (3) from the default of inch (2)
         extratags=[(296, 'H', 1, 3)])

  print ''
  print 'TIFF written to', outfile

def main(**kwargs):
  datafiles = kwargs.pop('datafiles')
  for datafile in datafiles:
    print 'Converting',datafile
    convert(datafile, **kwargs)

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Converts 2D SIOS scans to TIFF images')

  parser.add_argument('-row_step',
                      type=int,
                      default=1,
                      help='Step size when processing rows. row_step=2 skips every other row')
  parser.add_argument('-non_square_pixel',
                      action='store_true',
                      help='If given pixels will be non-square')

  parser.add_argument('-not_in_water',
                      action='store_true',
                      help='If given the refractive mismatch correction of 1.33 is not applied')
  parser.add_argument('datafiles', nargs='+', help='WZ data files')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))
