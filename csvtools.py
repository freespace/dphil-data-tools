#!/usr/bin/env python
from scipy.interpolate import interp1d
from scipy.optimize import leastsq

import numpy

"""
XXX: Many functions here are not suitable for general use, e.g. get_data.
Need to fix this eventually.
"""

def _fitx(xvec, yvec, yfunc):
  """
  This function computes the xoffset that yields the best fit between
  yvec and yfunc(xvec+xoffset)
  """
  def fitfunc(xoffset):
    newyvec = yfunc(xoffset+xvec)
    diff = newyvec - yvec
    return diff*diff

  return leastsq(fitfunc, 0.02)[0]

class CSVReader(object):
  def __init__(self, csvfile):
    super(CSVReader, self).__init__()

    self._csvfile = csvfile
    self._mat = None
    self._comments = None
    self._csv_source = None

  @property
  def csv_source(self):
    """
    Tries to infer where the csv file came from.

    Returns a string in CAPS identifying the source if possible, None
    otherwise.

    Note that a side effect of this function is that the entire CSV file is
    loaded.
    """

    # this acts as a safe guard and forces loading of csv if it has not yet
    # been loaded
    assert self.mat is not None

    return self._csv_source

  @property
  def comments(self):
    """
    Returns all the comments in a csvfile as a list. Comments are lines that
    start with #
    """
    if self._comments is None:
      headers = []
      with open(self._csvfile) as csvhandle:
        done = False
        while not done:
          line = csvhandle.readline()
          if line[0] == '#':
            line = line.strip()
            line = line.replace('\t',' ')
            headers.append(line)
          else:
            done = True
      self._comments = headers
    return self._comments

  @property
  def headers(self):
    """
    Returns the headers of a csvfile as a list. Headers are all lines that
    starts with #.

    This is misnamed and should not be used any more.
    """
    import sys
    sys.stderr.write('!! Do not use this headers property of CSVReader !!\n')

    return self.comments()

  @property
  def column_headers(self):
    """
    Returns the column headers, defined as the first line encountered that
    does is not a comment and contains one or more letters (a-z,A-Z). Headers
    are split on , and returned as a list. No support for quoting, thus no
    way to escape ,

    If the first line does not contain a letter, None is returned
    """
    with open(self._csvfile) as csvhandle:
      done = False
      while not done:
        line = csvhandle.readline()
        if line[0] != '#':
          for c in line:
            if c.isalpha():
              return map(str.strip,line.split(','))
          else:
            done = True
    return None

  @property
  def mat(self):
    def _load():
      return numpy.loadtxt(self._csvfile)

    def _load_SIOS():
      # files generated by SIOS control needs these settigns
      # import sys
      # sys.stderr.write('Loading SIOS data\n')
      self._csv_source = 'SIOS'
      with open(self._csvfile) as fh:
        lines = [line for line in fh if not line.startswith('#')]
        return numpy.loadtxt(lines, delimiter=',', skiprows=1)

    def _load_LECROYWR62Xi():
      self._csv_source = 'LECROYWR62Xi'
      with open(self._csvfile) as fh:
        lines = fh.readlines()
        # look for the first line containing a # which indicates
        # end of header
        while not lines[0].startswith('#'):
          lines.pop(0)

        return numpy.loadtxt(lines, delimiter=',', skiprows=2)

    # lazy load mat, b/c sometimes we just want the header
    if self._mat is None:
      loaders = (_load, _load_SIOS, _load_LECROYWR62Xi)
      mat = None
      exdict = dict()
      for loader in loaders:
        try:
          mat = loader()
        except Exception, ex:
          exdict[str(loader)] = ex
          # reset _csv_source as loaders set it as the first thing they
          # do. Technically not needed since the last loader to succeed
          # will set _csv_source properly, and seeing as as fail the
          # assert below if no loader succeeded, it ought not to matter.
          self._csv_source = None
          continue

      if mat is None:
        print 'Could not load CSV, following exception encountered:'
        for loader, ex in exdict.items():
          print loader+':', ex
        assert mat is not None, 'Could not load csv'

      self._mat = mat
    return self._mat

  def get_comment(self, commentprefix):
    """
    If any comment starts with the given prefix, then that comment is returned.
    Otherwise None is returned.
    """
    for comment in self.comments:
      if comment[1:].strip.startswith(commentprefix):
        return comment
    return None

  def get_header(self, headername):
    """
    Returns the named header in csvfile, or None if not found.

    e.g. to get the comment header, pass in 'Comment' for headername.

    Misnamed, do not use any more
    """
    return self.get_comment(headername)

  def get_header_value(self, headername):
    """
    Returns the value of the named header in csvfile, or None if header is not
    found.

    e.g. to get the value comment header, pass in 'Comment' for headername.
    """
    header = self.get_header(headername)
    if header:
      return header.split(':', 1)[1].strip()
    else:
      return None

  def get_start_time(self, index=0, formatted=False):
    """
    Returns the start time of when the scan at index started. Time is returned
    as Unix time.

    If formatted is true, then a str is returned representing the time in
    YYYY-mm-dd HH:mm:ss.

    Note that the time returned is _ALWAYS_ GMT time.
    """
    mat = self.mat

    # do we even have that many columns?
    if index <self.n_scans:
      isbackwardscan = index%2
      index *= 6
      tvec = mat[:,index+1]

      # because we 'flip' backward scans so the position increases with the
      # row number, this means for backward scans the start time is in fact
      # the last number, not the first.
      if isbackwardscan:
        ts = tvec[-1]
      else:
        ts = tvec[0]

      if formatted:
        import time
        return time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime(ts))
      else:
        return ts
    else:
      return None

  @property
  def n_scans(self):
    """
    Returns the number of scans in the CSV File
    """
    return self.mat.shape[1]//6

  def get_data(self, index=0):
    """
    index:  each file can contain multiple scans, and the first scan has index 0,
            the second scan has index 1, etc.

    Returns 5 numpy arrays corresponding to position vector, monitor PD, PMT
    bias, reflection PD, and PMT voltage. None is returned if there are no scans
    at the specified index or beyond.
    """
    mat = self.mat

    # do we even have that many columns?
    if index < self.n_scans:
      index *= 6
      xvec = mat[:,index+0]

      mon_vec = mat[:,index+2]
      bias_vec = mat[:,index+3]
      ref_vec = mat[:,index+4]
      pmt_vec = mat[:,index+5]

      return xvec, mon_vec, bias_vec, ref_vec, pmt_vec
    else:
      return None

  def get_averaged_data(self, xvec=None, traces=('mon', 'bias', 'ref', 'pmt')):
    """
    Like get_data(), but returns averages mapped to 0..10,000 with 50 steps on
    the x axis (20 apart). If xvec is given, it will be mapped onto that
    instead.

    Because the process is CPU intensive, only traces specified will be averaged.
    Unspecified traces are returned as None.

    e.g. if you pass in [1,2,3,4,5], then each series will be interpolated to get
    the y values at [1,2,3,4,5], then the average value at each x value will be
    computed and returned.

    Note that the averaged data might have peaks that is much smaller than
    expected, e.g. from 4.2 -> 3.8. This is because the peaks in the scans don't
    line up well enough to add on to each other. Binning based on PSF FWHM might
    solve this issue.
    """
    if xvec is None:
      xnew = numpy.linspace(0, 10000, 500)
    else:
      xnew = xvec

    domon = 'mon' in traces
    dobias = 'bias' in traces
    doref = 'ref' in traces
    dopmt = 'pmt' in traces

    monvecnew = numpy.zeros(len(xnew))
    biasvecnew = numpy.zeros(len(xnew))
    refvecnew = numpy.zeros(len(xnew))
    pmtvecnew = numpy.zeros(len(xnew))

    done = False
    index = 0
    while not done:
      data = self.get_data(index=index)
      if data is None:
        done = True
      else:
        xvec, monvec, biasvec, refvec, pmtvec = data
        def f(yvec, curyvec):
          yfunc = _interp(xvec, yvec, xnew)
          if index > 0:
            xoffset = _fitx(xvec, curyvec, yfunc)
            print 'fitted xoffset',xoffset
          else:
            xoffset = 0
          return yfunc(xvec+xoffset)

        # summy part of averaging
        if domon:
          monvecnew += f(monvec, monvecnew)

        if dobias:
          biasvecnew += f(biasvec, biasvecnew)

        if doref:
          refvecnew += f(refvec, refvecnew)

        if dopmt:
          pmtvecnew += f(pmtvec, pmtvecnew)

        index += 1

    # dividy part of averaging
    if domon:
      monvecnew /= index
    else:
      monvecnew = None

    if dobias:
      biasvecnew /= index
    else:
      biasvecnew = None

    if doref:
      refvecnew /= index
    else:
      refvecnew = None

    if dopmt:
      pmtvecnew /= index
    else:
      pmtvecnew = None

    return xnew, monvecnew, biasvecnew, refvecnew, pmtvecnew

def get_headers(csvfile):
  """
  Wrapper for CSVReader.headers
  """
  return CSVReader(csvfile).headers

def get_header(csvfile, headername):
  """
  Wrapper for CSVReader.get_header
  """
  return CSVReader(csvfile).get_header(headername)

def get_comment(csvfile, commentprefix):
  """
  Wrapper for CSVReader.get_comment
  """
  return CSVReader(csvfile).get_comment(commentprefix)

def get_header_value(csvfile, headername):
  """
  Wrapper for CSVReader.get_header_value
  """
  return CSVReader(csvfile).get_header_value(headername)

def get_start_time(csvfile, **kwargs):
  """
  Wrapper for CSVReader.get_start_time
  """
  return CSVReader(csvfile).get_start_time(**kwargs)

def get_data(csvfile, **kwargs):
  """
  Wrapper for CSVReader.get_data()
  """
  return CSVReader(csvfile).get_data(**kwargs)

def _interp(xvec, yvec, xnew):
  ymedian = numpy.median(yvec)
  interpf = interp1d(xvec, yvec, kind='cubic', bounds_error=False, fill_value=ymedian)
  return interpf

def get_averaged_data(csvfile, *args, **kwargs):
  """
  Wrapper for CSVReader.get_averaged_data
  """
  return CSVReader(csvfile).get_averaged_data(*args, **kwargs)
