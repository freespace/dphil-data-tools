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
from utils import keypress


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
    self.textkwargs = {
        'transform':self._ax.transAxes,
        'size': 11,
        }

    # tstart of the first trace
    self._tstart0 = self.t0

    # whether we are plotting a single csv file
    self._single = len(self.csvfiles) == 1

  def __getattr__(self, attr):
    if attr in self._kwargs:
      return self._kwargs[attr]
    else:
      raise AttributeError('No attribute named %s found'%(attr))

  def _get_save_to_filename(self, ext):
    filename = self.filename
    csvfiles = self.csvfiles
    suffix = ''
    if self.normalise:
      suffix += 'NR'
    if self.sub_y0:
      suffix += 'Y0'
    if self.sub_x0:
      suffix += 'X0'

    if len(suffix):
      suffix = '-'+suffix
    suffix += '.'+ext

    if filename is None:
      startfile = splitext(csvfiles[0])[0]
      if len(csvfiles) == 1:
        filename = startfile + suffix
      else:
        endfile = splitext(basename(csvfiles[-1]))[0]
        filename = startfile+'__'+endfile+suffix

    return filename

  def savefig(self, *args, **kwargs):
    if not 'bbox_inches' in kwargs is None:
      kwargs['bbox_inches'] = 'tight'

    self._fig.savefig(*args, **kwargs)
    print 'Plot saved to file:',args[0]

  def save_to_pdf(self):
    pdfname = self._get_save_to_filename('pdf')
    self.savefig(pdfname)

  def save_to_png(self):
    pngname = self._get_save_to_filename('png')
    self.savefig(pngname, dpi=300)

  def show(self):
    fig = self._fig

    fig.canvas.mpl_connect('key_press_event', keypress)

    # on OS X the tk window is behind everyone else by default, so we use
    # apple scripting to bring it to the front
    # http://stackoverflow.com/questions/1892339/make-tkinter-jump-to-the-front
    #
    # This stopped working for me in OS X 10.9.3, so I am disabling it
    #import sys
    #if sys.platform == 'darwin':
    #  import os
    #  os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')

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

    fig = self._fig
    ax = self._ax

    headers = ['']

    ylim = self.ylim

    if self.labels is None and len(csvfiles) > 1:
      # if no labels are specified and we have multiple
      # csv files, then when we plot it is confusing which
      # trace corresponds to which file. In these cases
      # we populate the labels with the basename of the csvfiles
      self.labels = map(basename, csvfiles)
      def shorten(s):
        if len(s) > 16:
          return s[:3]+'...'+s[-10:]
        else:
          return s
      self.labels = map(shorten, self.labels)

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
      else:
        lbl = None

      xvec = csv.mat[:,0]
      yvec = csv.mat[:,1]

      if self._kwargs.get('sub_x0', False):
        xvec -= xvec[0]
        
      xvec *= self.xmultiplier

      if self._kwargs.get('sub_y0', False):
        yvec -= yvec[0]

      if self.normalise:
        yrange = yvec.max() - yvec.min()
        yvec -= yvec.min()
        yvec /= yrange

      self._plot_traces(lbl, xvec, yvec)

      if self.normalise:
        ax.hlines(0.5, xvec.min(), xvec.max(), linestyles='dotted', colors=['gray'])

    if self.logy == True:
      ax.set_yscale('log')

    def _xylabel_by_source():
      if csv.csv_source == 'SIOS':
        return 'Z Position (mm)', 'Fluoresence (V)'
      else:
        return 'X LABEL', 'Y LABEL'

    xlabel, ylabel = _xylabel_by_source()
    if self.xlabel is not None:
      xlabel = self.xlabel
    if self.ylabel is not None:
      ylabel = self.ylabel

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if self.labels is not None:
      if len(self.labels) > 5:
        fontsize = 8
      else:
        fontsize = 11

      ax.legend(
          loc='upper right',
          ncol=1,
          prop={'size':fontsize})

    ax.set_title(title, size='medium')
    ax.set_autoscalex_on(False)

    # set x and y limits if given
    if self.xlim is not None:
      ax.set_xlim(self.xlim)

    yaxis = ax.get_yaxis()
    if self.hgrid or self.grid:
      yaxis.grid()
    ylim = yaxis.get_view_interval()

    xaxis = ax.get_xaxis()
    #xlim = xaxis.get_view_interval()
    if self.vgrid or self.grid:
      xaxis.grid()

    # plot headers
    if not no_debug:
      ax.text(
          0, 1.0,
          '\n'.join(headers),
          color='0.75',
          zorder=-1,
          verticalalignment='top',
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

  parser.add_argument('-sub_y0', action='store_true', help='If given, the first y value is subtracted from all y values')
  parser.add_argument('-sub_x0', action='store_true', help='If given, the first x value is subtracted from all x values')

  parser.add_argument('-xmultiplier', type=float, default=1, help='Value to multiplu x by before plotting')

  parser.add_argument('-pdf', action='store_true', default=False, help='Plot will be saved to PDF instead of being shown')
  parser.add_argument('-png', action='store_true', default=False, help='Plot will be saved to PNG instead of being shown')
  parser.add_argument('-filename', default=None, type=str, help='Name of output file to write to. Defaults to name of the first and last csv file joined by double underscore (__)')

  parser.add_argument('-xlabel', type=str, help='X label.')
  parser.add_argument('-ylabel', type=str, help='Y label.')
  parser.add_argument('-labels', type=str, nargs='+', help='Labels for each series to use in the legend. There must be one label per serie.')

  parser.add_argument('-normalise', action='store_true', default=False, help='If given, the y-values will be normalised to be between [0..1].')

  parser.add_argument('-logy', action='store_true', default=False, help='If given, the y-axis will be log')

  parser.add_argument('-ylim', type=float, nargs=2, default=None, help='If given, the y limits will be as given')
  parser.add_argument('-xlim', type=float, nargs=2, default=None, help='If given, the x limits will be as given')

  parser.add_argument('-hgrid', action='store_true', default=False, help='If given, horizontal grid will be added.')
  parser.add_argument('-vgrid', action='store_true', default=False, help='If given, vertical grid will be added.')
  parser.add_argument('-grid', action='store_true', default=False, help='If given, vertical grid will be added.')

  parser.add_argument('-figsize', type=float, nargs=2, default=None, help='If given, the figure size will be set as given, in inches')

  parser.add_argument('-interp', action='store_true', default=False, help='If given, each series will be interpolated using a cubic')

  parser.add_argument('-plotfile', type=str, default=None, help='A file containing the filenames of csvs to plot, along with optional title and comments')

  parser.add_argument('-skip', type=int, nargs=1, default=[0], help='When given a skip of n, every nth file is plotted, all other files with the exception of the first and last, is skipped.')

  parser.add_argument('-max_traces', type=int, nargs=1, default=[-1], help='When given, no more than max_traces number of traces will be plotted')
  parser.add_argument('-start_offset', type=int, nargs=1, default=[0], help='When given, the first start_offset number of files are ignored. This is applied before skip is applied')

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

  csvfiles = cmdargs['csvfiles']

  # apply start_offset
  start_offset = cmdargs['start_offset'][0]
  csvfiles = csvfiles[start_offset:]

  # apply skip
  skip = cmdargs['skip'][0]
  last = csvfiles[-1]
  csvfiles = csvfiles[0::skip+1]

  # apply max_traces
  max_traces = cmdargs['max_traces'][0]
  if max_traces >= 0:
    csvfiles = csvfiles[:max_traces]

  # we always want to plot the first and last file
  # XXX Do we?
  # if csvfiles[-1] != last:
  #  csvfiles.append(last)

  if len(csvfiles) < 1:
    print 'No files to plot: no files given or start_offset is too high or max_traces is 0'

  cmdargs['csvfiles'] = csvfiles

  p = Plot(**cmdargs)
  p.plot()

  shouldshow = True
  if cmdargs['pdf']:
    p.save_to_pdf()
    shouldshow = False

  if cmdargs['png']:
    p.save_to_png()
    shouldshow = False

  if shouldshow:
    p.show()

