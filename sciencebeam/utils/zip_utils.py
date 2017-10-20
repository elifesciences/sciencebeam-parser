import os
from stat import S_IXUSR

ZIP_UNIX_SYSTEM = 3

def make_executable(path):
  os.chmod(path, os.stat(path).st_mode | S_IXUSR)

def extract_all_with_permission(zf, target_dir):
  for info in zf.infolist():
    extracted_path = zf.extract(info, target_dir)

    if info.create_system == ZIP_UNIX_SYSTEM:
      unix_attributes = info.external_attr >> 16
      if unix_attributes:
        os.chmod(extracted_path, unix_attributes)

def extract_all_with_executable_permission(zf, target_dir):
  for info in zf.infolist():
    extracted_path = zf.extract(info, target_dir)

    if info.create_system == ZIP_UNIX_SYSTEM and os.path.isfile(extracted_path):
      unix_attributes = info.external_attr >> 16
      if unix_attributes & S_IXUSR:
        make_executable(extracted_path)
