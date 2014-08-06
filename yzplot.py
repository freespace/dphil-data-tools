"""
This file is a wrapper for plot_plane_using_scans.
"""
from matplotlib import pyplot as plt
from plot2d import plot_plane_using_scans

def plot_yz_plane_using_scans(scanIDs, yposvec, **imshowkwargs):
  """
  Plots YZ plane image using scans specified via scanIDs. The y position of
  each scan is given by yposvec, which is 1-1 matched to scanIDs.

  In addition to plotting, the result 2D array is also returned.

  If flip_x is given, scanIDs and yposvec are both reversed.

  Any unknown kwargs are passed onto imshow.
  """

  labels = ('Z position (mm)', 'Y position (mm)')

  ret = plot_plane_using_scans( scanIDs,
                                yposvec,
                                labels=labels,
                                **imshowkwargs)

  cb = plt.colorbar()
  cb.set_label('Fluorescence (V)')

  return ret
