#!/usr/bin/env python
"""
This script looks at the PSF and tells me the FWHM.
"""
import numpy as NP

from stats import get_stats
from csvtools import CSVReader

def main(filename, *args):
  csvreader = CSVReader(filename)
  mat = csvreader.mat

  xvec = mat[:,0]
  yvec = mat[:,1]
  sdict = get_stats(xvec, yvec, asdict=True)

  idxvec = yvec >= yvec.max()
  peakx = xvec[idxvec]
  print 'FWHM (um): %d\tz_peak (mm): %.3f'%(sdict['FWHM']*1000, peakx)

if __name__ == '__main__':
  import sys
  sys.exit(main(*sys.argv[1:]))

