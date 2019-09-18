import os
import pkg_resources


def get_office_script_directory():
    dist = pkg_resources.get_distribution("sciencebeam")
    return os.path.join(dist.location, 'sciencebeam/transformers/office_scripts')
