""""
This module provides function that can be used to plot
XZ or YZ planes by combining Z scans taken at different
X or Y positions
"""

from __future__ import division

from scipy.interpolate import interp1d
import numpy as np
import matplotlib.pyplot as plt

from csvtools import CSVReader

def get_csvs_by_scanID(scanID, workdir='.', require_ext=True):
  """
  In the current directory, or workdir.

  If require_ext is false, then files that do not end in .csv will also be
  considered.
  """
  from os import listdir
  entries = listdir(workdir)

  from os.path import isfile
  csvs = list()
  for entry in entries:
    if scanID in entry and isfile(entry):
      if require_ext and entry.endswith('csv') or not require_ext:
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
  csvfiles = get_csvs_by_scanID(scanID, workdir=workdir, require_ext=False)
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

def plot_plane_using_scans(scanIDs, posvec, labels=None, medium_n=1.33, imagej_compat=False, with_tics=False, scale=1.0, **imshowkwargs):
  """
  Plots a nZ plane image using scans specified via scanIDs, where n is one of
  X or Y. The position of each scan is given by posvec, which is 1-1 matched
  to scanIDs, and must be monotonic.

  The resulting image will have the correct aspect ratio and the correct size
  in inches, assuming posvec contains all measurements in mm, and all scans have
  z position recorded as mm. To save an image that has the same pixel size as
  microscope images, use a dpi equal to:

    25.4/<pixel size in um> * 1000

  Note that z axis will be multiplied by medium_n, which by default is
  1.33, that of water and the most common medium used.

  In addition to plotting, the result 2D array is also returned.

  labels should be a 2 tuple used to label the horizontal and vertical
  axis of the image.

  If imagej_compat is True, no interpolation will be done, and a gray colour map
  that maps to 0..10 will be used.

  If with_tics is True, then axis tics and labels will be added to the image.
  Note that if you use this, then you probably need to set scale to something
  like 50, or the figure, which is the same physical size as the image, will
  be too small to accomodate axes tics and such.

  Scale, defaults to 1.0. Image width and height is multiplied by this factor
  before plotting. Useful mostly when used with with_tics.

  Any unknown kwargs are passed onto imshow.

  Returned are:
    - commonZ: the Z axis values
    - ymat: the scans in matrix form, one scan per row
  """
  assert len(scanIDs) == len(posvec), 'Too many scanIDs for posvec, or the other way around'
  assert len(scanIDs) == len(set(scanIDs)), 'Duplicate scanID found'
  assert len(posvec) == len(set(posvec)), 'Duplicate xpos found'

  # ensure monotonicity of the posvec
  posvec = np.array(posvec)
  dposvec = posvec[1:] - posvec[:-1]
  s_dposvec = np.sign(dposvec)
  assert s_dposvec.max() == s_dposvec.min(), 'posvec is not monotonic!'

  # we require that posvec be sorted in descending order. Implicitly this also
  # requires scanIDs to be sorted in descending order
  if posvec[0] < posvec[-1]:
    posvec = posvec[::-1]
    scanIDs = scanIDs[::-1]

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

  # compute the width and height, accounting for medium refractive index
  zstart = commonz.min()
  zend = commonz.max()
  zrange = zend - zstart
  zend = zstart + zrange * medium_n

  extent = [zstart, zend, min(posvec), max(posvec)]

  # apply scaling, but backup the original first since these define
  # the actual physical extent of the image
  actualextent = extent
  extent = map(lambda x:x*scale, extent)

  # these are in mm
  width= extent[1] - extent[0]
  height = extent[3] - extent[2]

  # convert to inches
  width /= 25.4
  height /= 25.4

  # use given imshow args if present
  defimshowkwargs = {
      'interpolation':'bilinear',
      'cmap':'jet',
      'aspect':'auto',
      }
  defimshowkwargs.update(imshowkwargs)

  if not with_tics:
    fig = plt.figure(figsize=(width, height))
    ax = plt.Axes(fig, [0, 0, 1, 1])
    ax.set_axis_off()
  else:
    # add an extra 1.5 inch to accomodate tics and such
    newwidth = float(width) + 1.5
    newheight = float(height) + 1.5

    xoffset = 1
    xoffsetpc = xoffset / newwidth

    yoffset = 1
    yoffsetpc = yoffset / newheight

    widthpc = width / newwidth
    heightpc = height / newheight

    fig = plt.figure(figsize=(newwidth, newheight))
    ax = plt.Axes(fig, [xoffsetpc, yoffsetpc, widthpc, heightpc])
    
  fig.add_axes(ax)

  plt.imshow(ymat,
             extent=actualextent,
             **defimshowkwargs)

  if labels is not None:
    assert len(labels) == 2, 'Labels must be a 2 tuple'
    plt.xlabel(labels[0])
    plt.ylabel(labels[1])

  return commonz, ymat
