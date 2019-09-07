import os
import _fresh_eyes_script_utilities as feu

"""
Checks if a path is an actual file
Useful with argparse
"""
def is_filepath_or_tempfile(pth):
    if not os.path.isfile(pth):
        npth = os.path.join(feu.PTH_TEMP,pth)
        if os.path.isfile(npth):
            return os.path.abspath(os.path.realpath(os.path.expanduser(npth)))
        else:
            msg = "Given path is not a full file path, and was not found in the PTH_TEMP.\n{}".format(pth)
            raise argparse.ArgumentTypeError(msg)
    else:
        return os.path.abspath(os.path.realpath(os.path.expanduser(pth)))
