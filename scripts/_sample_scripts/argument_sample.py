import argparse

def main(object_of_anaconda_desire):
    print("my anaconda wants some {}".format(object_of_anaconda_desire))

if __name__ == '__main__' and __package__ is None:
    # ---- FEUTIL ---- #
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__)))) # add grandparent folder to the module search path
    import _fresh_eyes_script_utilities as feu # import fresh eyes fe_util
    # ---- FEUTIL ---- #

    # ---- ARGPARSE ---- #
    parser = argparse.ArgumentParser()
    parser.add_argument('what_the_anaconda_wants', help="the thing that your anaconda desires.")
    args = parser.parse_args()
    # ---- ARGPARSE ---- #

    main(args.what_the_anaconda_wants)
