#!/usr/bin/env python
from __future__ import division

import numpy as np

import dphil_paths

def main(**kwargs):
  datafiles = kwargs['datafiles']

  for datafile in datafiles:
    print_meta(datafile)

def get_meta(datafile, scandata=None, time_as_string=True):
  """
  If scandata is given, the datafile is ignored. Default None

  If time_as_string is True, starttime and endtime will be
  ctime strings, otherwise unix floats. Default True
  """

  if scandata is None:
    npzfile = np.load(datafile)
    scandata = npzfile['scandata'].item()

  if scandata.w is None:
    print datafile + ' does not define w axis, not processing.'
    return None

  zvec = scandata.zpositionvec
  wvec = scandata.wpositionvec

  wrange = wvec.max() - wvec.min()
  zrange = zvec.max() - zvec.min()

  pix = scandata.matrix
  pixsum = np.sum(pix)
  maxv = max(pix.flatten())
  minv = min(pix.flatten())

  zlim = (zvec[0], zvec[-1])
  wlim = (wvec[0], wvec[-1])

  firstzscan = scandata.zscandatavec[0][1]
  lastzscan = scandata.zscandatavec[-1][1]

  tstart = firstzscan.starttime
  tend = lastzscan.endtime
  xstartpos_um = firstzscan.xpos_um
  ystartpos_um = firstzscan.ypos_um

  LD_current_v = firstzscan.LDcurrentstart

  # pg 19 of LDC2xxC manual
  kctl_out = -10 / 200e-3
  LD_current = LD_current_v / kctl_out

  if time_as_string:
    from time import ctime
    tstart = ctime(tstart)
    tend = ctime(tend)
  metadata = dict(width=zrange,
                  height=wrange,
                  w=scandata.w,
                  instrument='SIOS',
                  source_file=datafile,
                  zlim=zlim,
                  wlim=wlim,
                  starttime=tstart,
                  endtime=tend,
                  wstep=wvec[1]-wvec[0],
                  zstep=zvec[1]-zvec[0],
                  comments=scandata.comments,
                  xstart_um=xstartpos_um,
                  ystart_um=ystartpos_um,
                  shape=pix.shape,
                  PMT_control_voltage_mV = firstzscan.PMTvoltagestart*1e3,
                  LD_current_mA = LD_current*1e3,
                  matrix_sum=pixsum
                  )
  return metadata

def print_meta(datafile):
  metadata = get_meta(datafile)
  for key,value in metadata.items():
    print key,"=", value

def parse_commandline_arguments():
  parser = get_commandline_parser()
  cmdargs = vars(parser.parse_args())
  return cmdargs

def get_commandline_parser():
  import argparse
  parser = argparse.ArgumentParser(description='Prints metadata information of WZ scans')
  parser.add_argument('datafiles', nargs='+', help='WZ data files')

  return parser

if __name__ == '__main__':
  parser = get_commandline_parser()
  cmdargs = parse_commandline_arguments()
  import sys
  sys.exit(main(**cmdargs))
