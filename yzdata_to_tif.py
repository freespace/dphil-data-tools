#!/usr/bin/env python

# we will need YZScanData from SIOS. Should fix this at some point
SIOS_PATH='../../code/SIOS_control'

# we will also need the stats module from data analysis tools
DATA_TOOLS_PATH='../../code/data_analysis_tools'

import sys
sys.path.insert(0, SIOS_PATH)
sys.path.insert(0, DATA_TOOLS_PATH)

import matplotlib
matplotlib.use('Qt4Agg')

import matplotlib.pyplot as plt
import numpy as np

def main(**kwargs):
  datafile = kwargs['datafile']
  npzfile = np.load(datafile)
  scandata = npzfile['scandata'].item()

  pix = scandata.matrix

  zvec = scandata.zpositionvec
  yvec = scandata.ypositionvec

  yrange = yvec.max() - yvec.min()
  zrange = zvec.max() - zvec.min()

  # correct for the fact these scans are taken in water, where the focus
  # travels 1.33 mm for every 1 mm the objective travels in air
  zrange *= 1.33

  pw = zrange/(len(zvec)-1)
  ph = yrange/(len(yvec)-1)

  print 'Image width=%.2f um, height=%.2f um'%(zrange+pw, yrange+ph)
  print '  pixel width=%.2f um, height=%.2f um'%(pw, ph)
  print '  pixel aspect ratio=%.2f (h:w=%.2f)'%(pw/ph, ph/pw)
  # pix is in volts (0..20) and we want to convert it to uint16 as follows:
  # n = (2**16-1)*v/20
  # Where n is the integer result, v is the voltage we have stored.

  intpix = (2**16-1)*pix/20
  intpix = intpix.astype(np.uint16)

  h,w = intpix.shape

  from PIL import Image
  im = Image.fromstring('I;16', (w, h), intpix.tostring())

  from os.path import splitext, extsep
  name,ext = splitext(datafile)
  outfile = name + extsep + 'tif'
  im.save(outfile)
  print 'TIFF written to', outfile

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='GNUplot replacement plotter')

  parser.add_argument('-squarepixels', 
                      action='store_true',
                      help='Scales the image so pixels are square. The smaller pixel dimension is stretched to match the larger pixel dimension')
  parser.add_argument('datafile', help='YZ data file')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  main(**cmdargs)
