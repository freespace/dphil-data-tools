#!/usr/bin/env python
from __future__ import division

"""
Computes the sum of PMT values over the entire image.
"""

import dphil_paths

def main(**kwargs):
  datafiles = kwargs.pop('datafiles')
  scan_interval = kwargs.pop('scan_interval')

  cols = ["Source Filename", "V. Section No.", "Total PMT Value", "Area (mm^2)", "PMT Density (total/area)"]
  if scan_interval is not None:
    cols.append("Elapsed Time")

  print '\t'.join(cols)


  for fileidx, datafile in enumerate(datafiles):
    from wzmeta import get_meta
    meta = get_meta(datafile)

    kwargs['pixel_height'] = meta['wstep']
    kwargs['pixel_width'] = meta['zstep']

    statsvec = get_sum(datafile, **kwargs)

    for stat in statsvec:
      secidx, pixsum, pixshape = stat

      # make secidx 1-based to match vindex
      secidx += 1

      # compute the *physical* size of the pixel area which is
      # um^2 because wstep and zstep are both in um
      pixarea_um = pixshape[0] * pixshape[1]

      # the above computation gives us a VERY big value, which
      # makes the density, which is fluorescence per um^2 very, and
      # this allows floating errors to creep in. Therefore, we divide
      # by 1e6 and convert from um^2 to mm^2
      pixarea_mm = pixarea_um / 1e6

      valuesvec = [datafile, secidx, pixsum, pixarea_mm, pixsum/pixarea_mm]
      if scan_interval is not None:
        valuesvec.append(fileidx*scan_interval)

      print '\t'.join(map(str, valuesvec))

def get_sum(datafile, vdivide=1, vindex=None, pixel_height=1, pixel_width=1):
  """
  Returns a list of (section-index, section-sum, section-shape) tuples, where
  sections are equal height divisions within an image. The number of sections
  depends on vdivide, with vdivide = 2 yielding 2 sections.

  If vindex is not None, then only the section whose 1-index is equal to vindex
  is returned.

  section-shape is the number of rows and columns, in that order, within each section,
  unless a value other than 1 is given for pixel_height and pixle_width, in which
  the returned value is (nrows * pixel_height, ncols * pixel_width).
  """

  import numpy as np
  npzfile = np.load(datafile)
  scandata = npzfile['scandata'].item()

  if scandata.w is None:
    print datafile + ' does not define w axis, not processing.'
    return None

  nrows, ncols = scandata.matrix.shape

  # note that this is an integer division, so will under-estimate
  # the number of rows needed by up to 1
  rowspersection = nrows // vdivide

  sectionstats = list()

  # remember that vindex is 1-based on the command line
  if vindex is not None:
    secidxvec = [vindex-1]
  else:
    secidxvec = xrange(vdivide)

  for secidx in secidxvec:
    startrow = secidx * rowspersection

    # because of integer truncation in the calculation of rowspersection,
    # when we calculate the last section we need to take up any remainders
    # by going all the way to the bottom
    if secidx + 1 < vdivide:
      endrow = startrow + rowspersection
    else:
      endrow = nrows

    section = scandata.matrix[startrow:endrow,:]

    shape = (section.shape[0] * pixel_height,
             section.shape[1] * pixel_width)

    sectionstats.append((secidx, np.sum(section), shape))

  return sectionstats

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Computes the sum of PMT values over the entire image')
  parser.add_argument('-vdivide', type=int, default=1, help='Divides the image vertically the specified number of times, outputting a sum for each section. Defaults to 1, equal to summing the whole image as one section')
  parser.add_argument('-vindex', type=int, default=None, help='If given in combination with vdivide, only the specified section (1...) will be summed.')
  parser.add_argument('-scan_interval', type=float, default=None, help='If given output will contain an additional column, Elapsed time, with a value for each scan of scan_interval*n, where n (0...) is index of the file amongst specified files')
  parser.add_argument('datafiles', nargs='+', help='WZ data files')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))
