import os, configparser
import _fresh_eyes_script_utilities.files


asci_eye = r"========== (o_o) Fresh Eyes =========="
print(asci_eye)


def load_config(section="DEFAULT"):
    config = configparser.ConfigParser()
    cfg = False
    pth_cfg = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) , 'config.ini' )
    try:
        with open(pth_cfg) as f:
            config.read(pth_cfg)
            try:
                cfg = config[section]
                print("Script running with feu.PTH_TEMP set to {}".format(cfg['PTH_TEMP']))
                if not os.path.isdir(cfg['PTH_TEMP']):
                    print("feu.PTH_TEMP is not a directory. Please create a directory at the location listed below or edit the config.ini file.\n{}".format(cfg['PTH_TEMP']))
                    exit()
            except Exception as e:
                print("Could not parse configuration file. Please format config.ini file as described at https://github.com/ksteinfe/fresh_eyes")
                print(e)
                exit()

    except IOError:
        print("Configuration file not found. Please create a config.ini file for the Fresh Eyes scripts as described at https://github.com/ksteinfe/fresh_eyes")
        exit()

    return cfg

# Do load the config file
cfg = load_config()
PTH_TEMP = cfg['PTH_TEMP']
