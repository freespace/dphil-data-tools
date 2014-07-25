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

def main(cmdargs):
  im = tiffany.open(cmdargs.tiff_file)
  infotag = 65330
  calibrationtag = 65326

  print 'Calibration (um):',im.im.ifd[calibrationtag][0]

  infolist = im.im.ifd[infotag]

  # info list seems to contain a 2 byte encoding with low byte first
  infolist = [a+b*0x100 for a,b in zip(infolist[0::2], infolist[1::2])]

  # it looks like Nikon is using windows-1252
  infostr = str()
  for b in infolist:
    try:
      infostr += chr(b).decode('windows-1252')
    except:
      if cmdargs.no_drop_chars:
        infostr += '&#%d;'%(b)

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
