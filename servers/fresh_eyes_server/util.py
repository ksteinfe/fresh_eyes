import os, io, base64, tempfile, uuid, shutil, configparser
from tensorflow.python.keras.applications.resnet50 import ResNet50, preprocess_input
from PIL import Image

# images recieved by API calls are saved locally, used for prediction, and then deleted
PTH_TMP = os.path.join(tempfile.gettempdir(),"fresh_eyes_temp_images")
print("temp location:{}\n".format(PTH_TMP))

def load_config(section):
    config = configparser.ConfigParser()
    cfg = False
    try:
        with open('config.ini') as f:
            config.read('config.ini')
            try:
                cfg = config[section]
                print("Fresh Eyes Server configured with port number {}".format(cfg['port_num']))
            except Exception as e:
                print("Could not parse configuration file. Please format config.ini file as described at https://github.com/ksteinfe/fresh_eyes")
                print(e)
                exit()

    except IOError:
        print("Configuration file not found. Please create a config.ini file for the Fresh Eyes Servers as described at https://github.com/ksteinfe/fresh_eyes")
        exit()

    return cfg


def save_temp_image(im):
    #TODO: is the PNG format an issue here?
    if not os.path.exists(PTH_TMP): os.makedirs(PTH_TMP)

    pth_im = os.path.join(PTH_TMP,"{}.jpg".format(str(uuid.uuid4())))
    im.save(pth_im)
    return(pth_im)

def req_string_to_image(s):
    try:
        data = base64.decodestring(bytes(s, 'utf-8'))
        im = Image.open(io.BytesIO(data))
        return im
    except Exception as e:
        #print(e)
        return False

def chan_count_to_mode(nc):
    if nc==1: return "L"
    if nc==3: return "RGB"
    if nc==4: return "RGBA"
    print("Encountered an unexpected number of channels ({})".format(nc))
    return False


def clear_temp_path():
    shutil.rmtree(PTH_TMP)

def get_resnet50(shape=(224, 224, 3)):
    return ResNet50(weights='imagenet', include_top=False, input_shape=shape)
