#!/usr/bin/env python
"""
This script looks at the PSF and tells me the FWHM.
"""
import numpy as NP

def main(filename, *args):
  data = NP.genfromtxt(
      filename,
      delimiter=",",
      dtype=float,
      skip_header=2,
      comments='#')
  if NP.isnan(NP.sum(data)):
    # failed to load psf data using default settings, assuming it is from
    # imageJ and thus tab delimited with no headers
    data = NP.genfromtxt(
        filename,
        dtype=float)

  if NP.isnan(NP.sum(data)):
    print 'nan in data file, aborting'
    return -1

  from stats import get_stats
  stats = get_stats(data[:,0], data[:,1], noauc=True)
  print stats
  FWHM, mode = stats[-2:]

  # find the x axis coordinate of when the peak occurs
  peakx = None
  for x,y in data[:]:
    if y >= stats[0]:
      peakx = x
      break

  print 'Peak:', stats[0], 'at x=', peakx

  peak = stats[0]
  median = stats[2]
  hm = 0.5*(peak+median)
  print 'FWHM:',FWHM, ' using ground = ', mode, 'half maximum=', hm


if __name__ == '__main__':
  import sys
  sys.exit(main(*sys.argv[1:]))

