import os
import pkg_resources


def get_office_script_directory():
    try:
        # with Apache Beam, __file__ might refer to the original file
        # rather than where it is installed to
        dist = pkg_resources.get_distribution("sciencebeam")
        return os.path.join(dist.location, 'sciencebeam/transformers/office_scripts')
    except pkg_resources.DistributionNotFound:
        # fallback to use __file__
        return os.path.dirname(__file__)
