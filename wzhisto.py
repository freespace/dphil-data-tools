#!/usr/bin/env python
from __future__ import division
"""
Plots histogram of SIOS 2D scans
"""

import os.path as op

import numpy as np
import matplotlib.pyplot as plt

import matplotlib_setup

import dphil_paths

def plot_histo(axis, values, vline, with_labels=True, bins=50):
  counts, bins, patches = axis.hist(values, bins=bins)

  if vline is not None:
    axis.vlines(vline, 0, counts.max(), colors=['red'], linewidth=1)

  if with_labels:
    axis.set_xlabel('Fluorescence Value (a.u.)')
    axis.set_ylabel('Count')

  return counts, bins
def main(**kwargs):
  datafile = kwargs.pop('datafile')
  vline = kwargs.pop('vline')
  pdf = kwargs.pop('pdf')
  threshold = kwargs.pop('threshold')
  inset_threshold = kwargs.pop('inset_threshold')

  import numpy as np
  npzfile = np.load(datafile)
  scandata = npzfile['scandata'].item()

  values = np.reshape(scandata.matrix, -1)

  if inset_threshold:
    counts, bins = plot_histo(plt.gca(), values, vline)
    # first arg is rect(left, bottom, width, height) where coords are normalised
    a2 = plt.axes([0.5, 0.5, 0.35, 0.35])
    values = values[values>threshold]
    bins = bins[bins>threshold]
    plot_histo(a2, values, vline, with_labels=False, bins=bins)
  else:
    plot_histo(plt.gca(), values[values>threshold], vline)

  if pdf:
    from os.path import splitext, extsep
    basename = splitext(datafile)[0] + '__histo'

    infoparts = list()
    if threshold:
      infoparts.append('TH%.2f'%(threshold))
    if vline:
      infoparts.append('VL%.2f'%(vline))
    if inset_threshold:
      infoparts.append('INSET')

    basename = '_'.join([basename]+infoparts)
    pdfname = basename + extsep + 'pdf'

    fig = plt.gcf()
    fig.savefig(pdfname, bbox_inches='tight')
    print 'PDF saved to', pdfname
  else:
    plt.show()


def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Plots histogram of intensity values in SIOS scans')
  parser.add_argument('datafile', type=str, help='WZ data file')
  parser.add_argument('-vline', type=float, help='Plots a vertical line at the specified X position')
  parser.add_argument('-threshold', type=float, default=0, help='Values below the threshold will be discarded')
  parser.add_argument('-inset_threshold', action='store_true', help='If given, thresholding will apply to a smaller inset histogram')
  parser.add_argument('-pdf', action='store_true', help='If given saves a copy of the plot as PDF without displaying it')
  parser.add_argument('-pdf_suffix', type=str, default=None, help='If given will be inserted just before .pdf with a leading _')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))
