import configparser, os, glob
from tqdm import tqdm
from tensorflow.python.keras.preprocessing import image
from tensorflow.python.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.python.keras.datasets import cifar10
from sklearn.model_selection import train_test_split
import numpy as np


def load_config(section):
    config = configparser.ConfigParser()
    cfg = False
    try:
        with open('config.ini') as f:
            config.read('config.ini')
            try:
                cfg = dict(config._sections[section])
                print("Fresh Eyes Trainer configured to train on the '{}' dataset stored at \n{}\n".format(cfg['data_to_train_on'], cfg['pth_tran']))
                if not os.path.isdir(cfg['pth_tran']): raise EnvironmentError("{} is not a directory on this computer.".format(cfg['pth_tran'] ))

                cfg['pth_data'] = os.path.join(cfg['pth_tran'],cfg['data_to_train_on'])
                if not os.path.isdir(cfg['pth_data']): raise EnvironmentError("{} is not a directory on this computer.".format(cfg['pth_data'] ))

                sub_dir_name = "{}-results".format(cfg['data_to_train_on'])
                if not os.path.isdir(cfg['pth_lobe_working']): raise EnvironmentError("{} is not a directory on this computer.".format(cfg['pth_lobe_working'] ))
                cfg['pth_model_save'] = os.path.join(cfg['pth_lobe_working'], sub_dir_name )

            except Exception as e:
                print("Could not parse configuration file. Please format config.ini file as described at https://github.com/ksteinfe/fresh_eyes")
                print(e)
                exit()

    except IOError:
        print("Configuration file not found. Please create a config.ini file for the Fresh Eyes Servers as described at https://github.com/ksteinfe/fresh_eyes")
        exit()

    key, val = 'epochs', 1
    if not key in cfg:
        print("The key '{}' was not found in the configuration file. Defaulting to a value of '{}'".format(key,val))
        cfg[key] = val
    cfg['epochs'] = int(cfg['epochs'])

    key, val = 'image_extension', 'png'
    if not key in cfg:
        print("The key '{}' was not found in the configuration file. Defaulting to a value of '{}'".format(key,val))
        cfg[key] = val

    key, val = 'test_train_split', 0.2
    if not key in cfg:
        print("The key '{}' was not found in the configuration file. Defaulting to a value of '{}'".format(key,val))
        cfg[key] = val
    cfg['test_train_split'] = float(cfg['test_train_split'])

    #print(cfg)
    return cfg



def get_local_images(image_path, test_train_split, img_fmt, target_size):
    classes = [dir for dir in os.listdir(image_path) if os.path.isdir(os.path.join(image_path,dir))]
    print("found {} classes: {}".format(len(classes), classes))
    input_arr = []
    target_labels = []
    for class_idx in range(len(classes)):
        #if not os.path.isdir(os.path.join(image_path, classes[class_idx])): continue
        paths = glob.glob(os.path.join(image_path, classes[class_idx]) + "/*.{}".format(img_fmt))
        print("found {} images with a .{} extension in {}".format(len(paths),img_fmt,os.path.join(image_path, classes[class_idx])))
        for img_path in tqdm(paths, desc=f'Processing label {classes[class_idx]}: '):
            img = image.load_img(img_path, target_size=target_size)
            x = image.img_to_array(img)
#             x = np.expand_dims(x, axis=0)
            x = preprocess_input(x)
            target_labels.append(class_idx)
            input_arr.append(x)
    X_train, X_test, y_train, y_test = train_test_split(input_arr, target_labels, test_size=test_train_split)
    X_train = np.array(X_train)
    X_test = np.array(X_test)
    y_train = np.array(y_train)
    y_test = np.array(y_test)
    return X_train, X_test, y_train, y_test, classes


def get_cifar10():
    (input_train, out_train), (input_test, out_test) = cifar10.load_data()
    return input_train, input_test, out_train, out_test, range(10)

def get_resnet50(shape=(224, 224, 3)):
    return ResNet50(weights='imagenet', include_top=False, input_shape=shape)




'''
def restrain_data(input_train, out_train, input_test, out_test, num_class, num_train, num_test, shape=(224, 224)):
    train_dict = defaultdict(list)
    test_dict = defaultdict(list)
    [train_dict[out_train[idx][0]].append(input_train[idx]) for idx in range(input_train.shape[0])]
    [test_dict[out_test[idx][0]].append(input_test[idx]) for idx in range(input_test.shape[0])]
    restrain_class = range(num_class)
    restrain_train = [[train_dict[i][idx], i] for idx in range(num_train) for i in restrain_class]
    restrain_test = [[test_dict[i][idx], i] for idx in range(num_test) for i in restrain_class]
    rand_train_idx = np.random.choice(num_train * num_class, num_train * num_class)
    rand_test_idx = np.random.choice(num_test * num_class, num_test * num_class)
    i_train = np.array([restrain_train[idx][0] for idx in rand_train_idx])
    o_train =  np.array([[restrain_train[idx][1]] for idx in rand_train_idx])
    i_test = np.array([restrain_test[idx][0] for idx in rand_test_idx])
    o_test =  np.array([[restrain_test[idx][1]] for idx in rand_test_idx])
    i_train = preprocess(i_train, shape=shape)
    i_test = preprocess(i_test, shape=shape)
    return i_train, i_test, o_train, o_test, restrain_class
'''



'''
def resize(arr, shape):
    return np.array(Image.fromarray(arr).resize(shape))

def decode_img(msg):
    msg = base64.b64decode(msg)
    buf = io.BytesIO(msg)
    img = Image.open(buf)
    return img

def preprocess(arr, shape=(224, 224)):
    arr = np.array([resize(arr[i], shape) for i in range(0, len(arr))]).astype('float32')
    arr = preprocess_input(arr)
    return arr

def freeze_layers(model, layer_num):
    for layer in model.layers[:layer_num]:
        layer.trainable = False

def train_layers(model, layer_num):
    for layer in model.layers[layer_num:]:
        layer.trainable = True
'''
