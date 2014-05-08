#!/usr/bin/env python
"""
Intended as a replacement for gnuplot. As such it supports different separator
characters, plotting multiple series, etc.

Since this script is intended for mywork there are certain presets which may
or may not be useful to a general user.
"""

from os.path import basename, splitext

import numpy as NP
from scipy.interpolate import interp1d
import matplotlib.pyplot as PLT

import csvtools as CSV
from utils import keypress, save_to_pdf


import itertools
linestyles = ['-', '-o', '-d', '-s', '-*']
linecolors = ['b', 'g', 'r', 'c', 'm', 'orange', 'k']
linespecs = list(itertools.product(linestyles, linecolors))
linespec_idx = 0

def reset_linespec():
  global linespec_idx
  linespec_idx = 0

def _next_linespec():
  global linespec_idx
  ls = linespecs[linespec_idx]
  linespec_idx = (linespec_idx+1)%len(linespecs)
  return ls

class Plot(object):
  def __init__(self, **kwargs):
    super(Plot, self).__init__()
    self._kwargs= kwargs

    # we can't use dict.get for these because the functions are evaluated
    # before calling get, and they have side effects
    self._fig = kwargs.get('fig')
    if self._fig is None:
      self._fig = PLT.figure()

    self._ax = kwargs.get('ax')
    if self._ax is None:
      self._ax =self._fig.add_subplot(111)

    self.plotkwargs = {
        'solid_capstyle':'butt',
        'markersize':4,
        'linewidth':1.2,
        }
    self.textkwargs = {'transform':self._ax.transAxes}

    # tstart of the first trace
    self._tstart0 = self.t0

    # whether we are plotting a single csv file
    self._single = len(self.csvfiles) == 1

  def __getattr__(self, attr):
    if attr in self._kwargs:
      return self._kwargs[attr]
    else:
      raise AttributeError('No attribute named %s found'%(attr))

  def save_to_pdf(self):
    pdfname = self.pdfname
    csvfiles = self.csvfiles
    if pdfname is None:
      startfile = splitext(csvfiles[0])[0]
      if len(csvfiles) == 1:
        pdfname = startfile + '.pdf'
      else:
        endfile = splitext(basename(csvfiles[-1]))[0]
        pdfname = startfile+'__'+endfile+'.pdf'

    save_to_pdf(self._fig, pdfname)

  def show(self):
    fig = self._fig

    fig.canvas.mpl_connect('key_press_event', keypress)

    # on OS X the tk window is behind everyone else by default, so we use
    # apple scripting to bring it to the front
    # http://stackoverflow.com/questions/1892339/make-tkinter-jump-to-the-front
    import sys
    if sys.platform == 'darwin':
      import os
      os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')

    PLT.show()

  def _make_tstart_label(self, tstart):
    if self._tstart0 is None:
      self._tstart0 = tstart
    tstart -= self._tstart0
    return 't=%.1f s'%(tstart)

  def _plot_traces(self, lbl, xvec, yvec):
    xnew = xvec
    ynew = yvec
    if self.interp == True:
      # first down sample to smooth out the data
      interpf = interp1d(xvec, yvec, kind='cubic')
      xnew = NP.linspace(xvec.min(), xvec.max(), len(xvec)/2)
      ynew = interpf(xnew)

      # now up sample it to make it it look smooth
      interpf = interp1d(xnew, ynew, kind='cubic')
      xnew = NP.linspace(xvec.min(), xvec.max(), len(xvec))
      ynew = interpf(xnew)

    l = None

    # give precedence to generated or user supplied labels
    if lbl is not None:
      l = lbl

    ls, lc = _next_linespec()
    self._ax.plot(xnew, ynew, ls, color=lc, label=l, **self.plotkwargs)

  def plot(self):
    csvfiles = self.csvfiles
    title = self.title
    comment_title = self.comment_title
    no_debug = self.no_debug
    tstart = self._tstart0

    fig = self._fig
    ax = self._ax

    headers = ['']

    ylim = self.ylim
    if ylim is not None:
      ax.set_autoscaley_on(False)
      ax.set_ylim(ylim)

    for csvidx in xrange(len(csvfiles)):
      csvfile = csvfiles[csvidx]
      print 'Plotting',csvfile
      csv = CSV.CSVReader(csvfile)

      headers += ['# File: '+basename(csvfile)]
      if self._single:
        headers.extend(csv.comments)

      if csvidx == 0 and comment_title and len(title) == 0:
        title = csv.get_comment(csvfile, 'Comment')

      if self.labels is not None:
        lbl = self.labels[csvidx]
      elif not self._single:
        lbl = self._make_tstart_label(tstart)
      else:
        lbl = None

      xvec = csv.mat[:,0]
      yvec = csv.mat[:,1]
      self._plot_traces(lbl, xvec, yvec)

    if self.logy == True:
      ax.set_yscale('log')

    xlabel = self._kwargs.get('xlabel', 'X LABEL')
    ylabel = self._kwargs.get('ylabel', 'Y LABEL')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if not self.nolegend == True and self.labels is not None:
      ax.legend(loc=1, ncol=1, prop={'size':11})

    ax.set_title(title, size='medium')
    ax.set_autoscalex_on(False)

    # set x and y limits if given
    if self.xlim is not None:
      ax.set_xlim(self.xlim)

    yaxis = ax.get_yaxis()
    yaxis.grid()
    ylim = yaxis.get_view_interval()

    #xaxis = ax.get_xaxis()
    #xlim = xaxis.get_view_interval()

    # plot headers
    if not no_debug:
      ax.text(
          0, 0.2,
          '\n'.join(headers),
          color='0.7',
          zorder=-1,
          verticalalignment = 'bottom',
          **self.textkwargs)

    # resize the plot if figsize is given
    if self.figsize is not None:
      fig.set_size_inches(*self.figsize, forward=True)
      PLT.tight_layout()

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='GNUplot replacement plotter')

  parser.add_argument('-title', default='', help='Plot title')
  parser.add_argument('-comment_title', action='store_true', help='If given, the comment of the first csv file will be used as plot title. This is ignored if title is given.')

  parser.add_argument('-show_start_time', action='store_true', help='If given, the time of the first csv file will be shown as a label in the top-right.')
  parser.add_argument('-t0', type=float, default=None, help='Value to use as t=0 when displaying time points on the x-axis.')
  parser.add_argument('-x0', type=float, default=None, help='Value to use as x=0 when displaying positions on the x-axis. ')
  parser.add_argument('-no_debug', action='store_true', help='If given, file comments and filenames will not be added to plots.')

  parser.add_argument('-pdf', action='store_true', default=False, help='Plot will be saved to PDF instead of being shown')
  parser.add_argument('-pdfname', default=None, type=str, help='Name of pdf file to write to. Defaults to name of the first and last csv file joined by double underscore (__)')

  parser.add_argument('-labels', type=str, nargs='+', help='Labels for each series to use in the legend. There must be one label per serie.')

  parser.add_argument('-logy', action='store_true', default=False, help='If given, the y-axis will be log')
  parser.add_argument('-ylim', type=float, nargs=2, default=None, help='If given, the y limits will be as given')

  parser.add_argument('-xlim', type=float, nargs=2, default=None, help='If given, the x limits will be as given')

  parser.add_argument('-figsize', type=float, nargs=2, default=None, help='If given, the figure size will be set as given, in inches')

  parser.add_argument('-interp', action='store_true', default=False, help='If given, each series will be interpolated using a cubic')

  parser.add_argument('-nolegend', action='store_true', default=False, help='If given, no legend will be plotted')

  parser.add_argument('-plotfile', type=str, default=None, help='A file containing the filenames of csvs to plot, along with optional title and comments')

  parser.add_argument('-skip', type=int, nargs=1, default=[0], help='When given a skip of n, every nth file is plotted, all other files with the exception of the first and last, is skipped.')

  parser.add_argument('csvfiles', nargs='*', help='CSV files to plot')

  return parser


if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()

  plotfile = cmdargs['plotfile']
  if plotfile:
    from plotfiletools import parse_plotfile
    csvfiles, moreargs = parse_plotfile(plotfile)
    import sys

    # this order should give precedence to commandline args
    newargs = moreargs + sys.argv[1:]
    cmdargs = vars(parser.parse_args(newargs))
    l = cmdargs.get('csvfiles')
    if l is None:
      cmdargs['csvfiles'] = csvfiles
    else:
      l.extend(csvfiles)

  # apply skip
  csvfiles = cmdargs['csvfiles']
  skip = cmdargs['skip'][0]
  last = csvfiles[-1]
  csvfiles = csvfiles[0::skip+1]

  # we always want to plot the first and last file
  if csvfiles[-1] != last:
    csvfiles.append(last)

  cmdargs['csvfiles'] = csvfiles

  p = Plot(**cmdargs)
  p.plot()
  if cmdargs['pdf']:
    p.save_to_pdf()
  else:
    p.show()

