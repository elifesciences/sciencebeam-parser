import os
import errno

def makedirs(path, exists_ok=False):
  try:
    # Python 3
    os.makedirs(path, exists_ok=exists_ok)
  except TypeError:
    # Python 2
    try:
      os.makedirs(path)
    except OSError as e:
      if e.errno == errno.EEXIST and os.path.isdir(path) and exists_ok:
        pass
      else:
        raise
