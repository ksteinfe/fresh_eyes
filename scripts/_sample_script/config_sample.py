

def main():
    print("my anaconda still don't want none")

if __name__ == '__main__' and __package__ is None:
    # ---- FEUTIL ---- #
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__)))) # add grandparent folder to the module search path
    import _fresh_eyes_script_utilities as feu # import fresh eyes fe_util
    # ---- FEUTIL ---- #

    main()
