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
  try:
    listofbytes = map(int, listofbytes)
    codes = [0xff&a|b<<8 for a,b in zip(listofbytes[0::2], listofbytes[1::2])]
    ret = str()
    for b in codes:
      try:
        ret += chr(b).decode('windows-1252')
      except:
        if nodropchars:
          ret += '&#x%04x;'%(0xffff&b)
  except:
    if len(listofbytes):
      print len(listofbytes)
      ret = listofbytes
    else:
      ret = '##<no data>##'

  return ret
  
def main(cmdargs):
  for tifffile in cmdargs.tiff_files:
    print tifffile+':',
    im = tiffany.open(tifffile)
    infotag = 65330
    calibrationtag = 65326

    def d(l):
      return _decode(l, cmdargs.no_drop_chars)

    if cmdargs.dump_tags:
      if im.im.ifd.get(calibrationtag) is None:
        for tag in im.im.ifd.keys():
          print '===== tag' + str(tag) + ' ====='
          print d(im.im.ifd[tag])
          print ''
    else:
      print 'Pixel size (um):',im.im.ifd.get(calibrationtag, ['Not Available'])[0]

      if cmdargs.info:
        infolist = im.im.ifd[infotag]
        infostr = d(infolist)

        # I have no idea how Nikon is encoding this stuff, but it looks like I can
        # split on the words TextInfoItem_ and get away with it
        infovec = infostr.split('TextInfoItem_')

        for idx, info in enumerate(infovec):
          prefix = str(idx+1)
          print '\tInfo %d: %s'%(idx+1, info[len(prefix):])

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='Program to readout text metadata from Nikon NIS tiffs')

  parser.add_argument('-no-drop-chars', action='store_true', help='If given, characters which cannot be decoded will be printed')
  parser.add_argument('-info', action='store_true', help='If given, text information metadata will also be printed')
  parser.add_argument('-dump_tags', action='store_true', help='If given, prints all available tags. Nullifies -extras.')
  parser.add_argument('tiff_files', nargs='+', help='tiff files to parse')

  cmdargs = parser.parse_args()
  main(cmdargs)
