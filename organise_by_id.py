#!/usr/bin/env python

"""
This script organises a file full of SIOS scan files into directories
based on the phantom ID.
"""

import os

npz_vec = filter(lambda x:x.endswith('npz'), os.listdir('.'))

def get_phantom_id(filename):
  return filename.split('-')[3]

phantom_id_vec = set()
for npz in npz_vec:
  phantom_id_vec.add(get_phantom_id(npz))

print 'Got phantom IDs', phantom_id_vec

for phantom_id in phantom_id_vec:
  print 'Organising id-'+phantom_id

  # create a dir if needed
  dirname = 'id-'+phantom_id
  if os.path.exists(dirname):
    assert os.path.isdir(dirname)
    print '\tdir exists'
  else:
    os.mkdir(dirname)
    print '\tdir created'

  import shutil
  for npz in npz_vec:
    if get_phantom_id(npz) == phantom_id:
      dst = os.path.join(dirname, npz)
      shutil.move(npz, dst)
      print '\tmoved %s to %s'%(npz, dst)
