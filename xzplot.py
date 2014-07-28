from scipy.interpolate import interp1d
import numpy as np
import matplotlib.pyplot as plt

from csvtools import CSVReader

def get_csvs_by_scanID(scanID, workdir='.'):
  """
  In the current directory, or workdir.
  """
  from os import listdir
  entries = listdir(workdir)

  from os.path import isfile
  csvs = list()
  for entry in entries:
    if scanID in entry and isfile(entry) and entry.endswith('csv'):
      csvs.append(entry)

  return csvs

def get_xyvec_from_csv(csvfilename):
  print 'Loading', csvfilename
  mat = CSVReader(csvfilename).mat
  xvec = mat[:,0]
  yvec = mat[:,1]

  return xvec, yvec

def get_xvec_yfunc_from_scan(scanID, workdir='.'):
  """
  Loads all data from the specified scan, and returns an xvec that is common
  to all csvs, and a function that returns the average interpolated y value
  for any value within xvec.

  All data is first resampled to the same x-axis grid, then averaged.
  """
  csvfiles = get_csvs_by_scanID(scanID, workdir=workdir)
  assert len(csvfiles) > 0, 'Scan %s not found in %s'%(scanID, workdir)

  yfuncvec = list()
  max_xstart = 0
  min_xend = 2**32
  min_xcount = 2**32

  for csv in csvfiles:
    xvec, yvec = get_xyvec_from_csv(csv)
    yfunc = interp1d(xvec, yvec)
    yfuncvec.append(yfunc)

    # need to use min/max here because some scans are done backwards, such that
    # xvec[0]> xvec[-1]
    max_xstart = max(max_xstart, xvec.min())
    min_xend = min(min_xend, xvec.max())
    min_xcount = min(min_xcount, len(xvec))

  commonx = np.linspace(max_xstart, min_xend, min_xcount)

  def avgyfunc(x):
    ysum = 0
    for yfunc in yfuncvec:
      ysum+= yfunc(x)
    ysum /= len(yfuncvec)
    return ysum

  # make sure our commonx range really is valid for avgyfunc
  assert avgyfunc(commonx[0]) is not None
  assert avgyfunc(commonx[-1]) is not None

  return commonx, avgyfunc

def plot_xz_plane_using_scans(scanIDs, xposvec, flip_x=False, **imshowkwargs):
  """
  Plots XZ plane image using scans specified via scanIDs. The x position of
  each scan is given by xposvec, which is 1-1 matched to scanIDs.

  In addition to plotting, the result 2D array is also returned.

  If flip_x is given, scanIDs and xposvec are both reversed.

  Any unknown kwargs are passed onto imshow.
  """
  assert len(scanIDs) == len(xposvec), 'Too many scanIDs for xposvec, or the other way around'
  assert len(scanIDs) == len(set(scanIDs)), 'Duplicate scanID found'
  assert len(xposvec) == len(set(xposvec)), 'Duplicate xpos found'

  if flip_x:
    scanIDs = scanIDs[::-1]
    xposvec = xposvec[::-1]

  max_xstart = 0
  min_xend = 2**32
  min_xcount = 2**32

  yfuncvec = list()
  for scanID in scanIDs:
    xvec, yfunc = get_xvec_yfunc_from_scan(scanID)
    yfuncvec.append(yfunc)
    max_xstart = max(max_xstart, xvec[0])
    min_xend = min(min_xend, xvec[-1])
    min_xcount = min(min_xcount, len(xvec))

  commonx = np.linspace(max_xstart, min_xend, min_xcount)

  ymat = np.concatenate(list(yfunc(commonx) for yfunc in yfuncvec))
  ymat.shape = (len(scanIDs), min_xcount)

  # ok, time to swap terminology. In the data so far, x is really z, so lets
  # rename accordingly
  commonz = commonx
  

  if not 'aspect' in imshowkwargs:
    imshowkwargs['aspect'] = 'auto'

  plt.imshow(ymat,
             extent=[commonz.min(), commonz.max(), xposvec[0], xposvec[-1]],
             **imshowkwargs)

  return commonz, ymat

