#!/usr/bin/env python
"""
Plots one or more csv files produced by F410_control.py.

In addition to specifying CSVs to plot, a plotfile may be specified instead.
A plot file is a file that contains a list of CSVs to plot, in order. Comments
can be added to a plot file by starting a line with #.

Command line arguments can also be given in plot files. Any time a line starting
with #! is encountered, the rest of the line will be parsed as if it was given
on the command line. e.g. the following specifies the title:

  #! -title 'A title'

For convenience, plot files accept csv filenames in the format grep produces,
e.g.

  2013-08-30_OE2K.csv:# Comment: sodium azide0.002% w/v, 1% w/v agar, in air, y=0.0

Is acceptable
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
      PLT.figure()

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

  def _plot_traces(self, lbl, tstart, xvec, mon_vec, bias_vec, ref_vec, pmt_vec):
    def p(yvec, name):
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
      elif name is not None:
        l = name

      ls, lc = _next_linespec()
      self._ax.plot(xnew, ynew, ls, color=lc, label=l, **self.plotkwargs)

    if filter(lambda x:x, map(self._kwargs.get, ['mon','bias','ref','pmt'])) == []:
      p(mon_vec, 'mon')
      p(bias_vec, 'bias')
      p(ref_vec, 'ref')
      p(pmt_vec, 'pmt')
    else:
      if self.mon:
        p(mon_vec, 'mon')

      if self.bias:
        p(bias_vec, 'bias')

      if self.ref:
        p(ref_vec, 'ref')

      if self.pmt:
        p(pmt_vec, 'pmt')

  def plot(self):
    csvfiles = self.csvfiles
    labels = self.labels
    title = self.title
    comment_title = self.comment_title
    show_start_time = self.show_start_time
    do_average = self.average
    no_debug = self.no_debug

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
        headers.extend(csv.headers)

      if csvidx == 0 and comment_title and len(title) == 0:
        title = csv.get_header_value(csvfile, 'Comment')

      # get the start time of the first scan, which is the start time of the
      # series of scans contained in the file
      tstart = csv.get_start_time()

      if self.labels is not None:
        lbl = self.labels[csvidx]
      elif not self._single:
        lbl = self._make_tstart_label(tstart)
      else:
        lbl = None

      traces = filter(self._kwargs.get, ['mon','bias','ref','pmt'])

      if do_average:
        assert len(traces) == 1, '%d averages requested when only one and exactly one is allowed: %s'%(len(traces), traces)
        xvec, mon_vec, bias_vec, ref_vec, pmt_vec = csv.get_averaged_data(traces=traces)
        self._plot_traces(lbl, tstart, xvec, mon_vec, bias_vec, ref_vec, pmt_vec)
      else:
        index = self.index
        if index == 'all':
          indicies = list(xrange(csv.n_scans))
        elif index == 'last':
          indicies = [csv.n_scans-1]
        elif index == 'even':
          indicies = list(xrange(csv.n_scans))
          indicies = filter(lambda x: x%2==0, indicies)
        elif index == 'odd':
          indicies = list(xrange(csv.n_scans))
          indicies = filter(lambda x: x%2==1, indicies)
        elif ',' in index:
          indicies = map(int, index.split(','))
        else:
          indicies = [int(index)]

        for index in indicies:
          xvec, mon_vec, bias_vec, ref_vec, pmt_vec = csv.get_data(index=index)

          # get start time of this scan to compute the time since t0
          tstart = csv.get_start_time(index=index)

          # use start time as label only if we are plotting a single trace
          # e.g. pmt trace, and we are plotting more than one scan
          # If t0 was given however, then we always plot the time stamp
          # regardless of all else
          if len(traces) == 1 and len(indicies) > 1 or self.t0 is not None:
            lbl = self._make_tstart_label(tstart)
          else:
            lbl = None
          self._plot_traces(lbl, tstart, xvec, mon_vec, bias_vec, ref_vec, pmt_vec)

          # plot start time if needed, but only for first file
          if csvidx ==0 and show_start_time:
            ax.text(
                0, 1,
                '\n# '+csv.get_start_time(index=index, formatted=True),
                verticalalignment = 'top',
                **self.textkwargs)

    if self.logy == True:
      ax.set_yscale('log')

    xlabel = self._kwargs.get('xlabel', 'Position (um)')
    ylabel = self._kwargs.get('ylabel', 'Voltage (V)')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if not self.nolegend == True:
      ax.legend(loc=1, ncol=1, prop={'size':11})

    ax.set_title(title, size='medium')
    ax.set_autoscalex_on(False)

    # set x and y limits if given
    if self.xlim is not None:
      ax.set_xlim(self.xlim)
    else:
      ax.set_xlim([0, 10000])

    yaxis = ax.get_yaxis()
    yaxis.grid()
    ylim = yaxis.get_view_interval()

    xaxis = ax.get_xaxis()
    xlim = xaxis.get_view_interval()

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
  parser = argparse.ArgumentParser(description='Plots standard F410 scan data')
  parser.add_argument('-ref', action='store_true', help='Plot reflection')
  parser.add_argument('-mon', action='store_true', help='Plot monitor')
  parser.add_argument('-pmt', action='store_true', help='Plot PMT')
  parser.add_argument('-bias', action='store_true', help='Plot bias')

  parser.add_argument('-title', default='', help='Plot title')
  parser.add_argument('-comment_title', action='store_true', help='If given, the comment of the first csv file will be used as plot title. This is ignored if title is given.')

  parser.add_argument('-show_start_time', action='store_true', help='If given, the time of the first csv file will be shown as a label in the top-right.')
  parser.add_argument('-t0', type=float, default=None, help='Unix time to use as t=0 when calculating relative timestamps')
  parser.add_argument('-no_debug', action='store_true', help='If given, file comments and filenames will not be added to plots.')

  parser.add_argument('-pdf', action='store_true', default=False, help='Plot will be saved to PDF instead of being shown')
  parser.add_argument('-pdfname', default=None, type=str, help='Name of pdf file to write to. Defaults to name of the first and last csv file joined by double underscore (__)')

  parser.add_argument('-index', type=str, default='0', help="""
    Index of scan to plot, pass "all" to plot all indicies. Multiple indicies
    can be specified by separating with ",". e.g. "1,2,3,4". Additionally
    "even", "odd", and "last" are also supported
  """)
  parser.add_argument('-average', action='store_true', help='If given, all scans from a file will be combined by averaging and plotted as a single  series')

  parser.add_argument('-labels', type=str, nargs='+', help='Labels for each series to use in the legend. There must be one label per file.')

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

