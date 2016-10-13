#!/usr/bin/env python
from __future__ import division

import numpy as np

import dphil_paths
from debug_print import pln

"""
Attempts to convert data from matlab fig files into numpy npz files
"""

def main(fig_file=None, debug=False):
  from scipy.io import loadmat
  figmat = loadmat(fig_file, struct_as_record=False, squeeze_me=True)
  fig = figmat['hgS_070000']

  assert fig.children.type == 'axes', 'Fig file structure not yet supported'

  xvec = None
  yvec = None
  xlabel = None
  ylabel = None

  for c in fig.children.children:
    if c.type == 'graph2d.lineseries':
      pln('Found graph2d.lineseries')
      if xvec is None and yvec is None:
        xvec = c.properties.XData
        yvec = c.properties.YData
        pln('XData has %d entries'%(len(xvec)))
        pln('YData has %d entries'%(len(yvec)))
      else:
        pln('Extra graph2d.lineseries found, ignoring')

    if c.type == 'text':
      if xlabel is None:
        xlabel = c.properties.String
        pln('X label: %s'%(xlabel))
      elif ylabel is None:
        ylabel = c.properties.String
        pln('Y label: %s'%(ylabel))

  matrix = np.column_stack((xvec, yvec))

  if debug:
    import matplotlib.pyplot as plt
    import matplotlib_setup
    from utils import keypress
    plt.plot(xvec, yvec)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    plt.gcf().canvas.mpl_connect('key_press_event', keypress)
    plt.show()
    plt.close()
  else:
    # save file here
    npzfile = fig_file+'.npz'
    np.savez(npzfile, data=matrix, source='fig2npz.py', xlabel=xlabel, ylabel=ylabel)
    pln('Saved to %s'%(npzfile))

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Converts 2D SIOS scans to TIFF images')
  parser.add_argument('-debug',
                      action='store_true',
                      help='If given the extracted data is plotted and not saved')

  parser.add_argument('fig_file', help='Matlab fig files')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))

