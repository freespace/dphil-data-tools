#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 25 22:26:29 2014

Nikon NIS Elements adds text metadata to its files which CANNOT be read by
anything reasonble, e.g. ImageJ, GIMP.

To that end this program was created. It will read off tag 65330 which stores
most of text metadata, and prints it out.

Since this is reverse engineered, there will be mistakes, but it is useful
enough as-is.

Note that there is also embedded XML information, which I am leaving out for
now because I don't need it. You can however find it in 65332.

@author: @freespace
"""
import tiffany

def _decode(listofbytes, nodropchars):
  """
  nodropchars: if True, then undecodable values are part of the returned
  string, otherwise they are silently dropped
  """
  # strings appear to be stored as windows-1252 across 2 bytes
  codes = [a+b*0x100 for a,b in zip(listofbytes[0::2], listofbytes[1::2])]
  ret = str()
  for b in codes:
    try:
      ret += chr(b).decode('windows-1252')
    except:
      if nodropchars:
        ret += '&#x%x;'%(b)
  return ret
  
def main(cmdargs):
  im = tiffany.open(cmdargs.tiff_file)
  infotag = 65330
  calibrationtag = 65326
  extratag = 65331

  print 'Calibration (um):',im.im.ifd[calibrationtag][0]

  def d(l):
    return _decode(l, cmdargs.no_drop_chars)

  infolist = im.im.ifd[infotag]
  infostr = d(infolist)

  extralist = im.im.ifd[extratag]
  extrastr = d(extralist)

  print extrastr
  return

  # I have no idea how Nikon is encoding this stuff, but it looks like I can
  # split on the words TextInfoItem_ and get away with it
  infovec = infostr.split('TextInfoItem_')

  for idx, info in enumerate(infovec):
    prefix = str(idx+1)
    print 'Info %d: %s'%(idx+1, info[len(prefix):])

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='Program to readout text metadata from Nikon NIS tiffs')

  parser.add_argument('-no-drop-chars', action='store_true', help='If given, characters which cannot be decoded will be printed')
  parser.add_argument('tiff_file', type=str, help='tiff file to parse')

  cmdargs = parser.parse_args()
  main(cmdargs)
