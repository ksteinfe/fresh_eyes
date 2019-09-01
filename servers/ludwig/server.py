import os, logging, shutil, time, json, configparser
import tempfile, uuid
import io, base64
from PIL import Image

from flask import Flask
from flask import request
from collections import OrderedDict
from flask_cors import CORS

print("...importing Ludwig")
from ludwig import LudwigModel

ROUND_FLOATS_TO = 10

# images recieved by API calls are saved locally, used for prediction, and then deleted
PTH_TMP = os.path.join(tempfile.gettempdir(),"ludwig_server_temp_images")

###############################################################
##                                                           ##
##                          INIT                             ##
##                                                           ##
###############################################################
MODL, MMTA, FEAS_IN, FEAS_OUT = False, False, False, False
app = Flask("Fresh Eyes API")
CORS(app)

def initialize(config):
    pth_mdl = os.path.join( config['pth_mdls'], config['model_to_load'], "model")
    if not os.path.isdir(pth_mdl):
        raise Exception("Could not find the model specified in the models directory: {}".format(pth_mdl))


    global MODL, MMTA, FEAS_IN, FEAS_OUT
    # load a model
    st = time.time()
    print("...loading model from {}".format(pth_mdl))
    MODL = LudwigModel.load(pth_mdl)
    with open(os.path.join(pth_mdl,"train_set_metadata.json")) as f: MMTA = json.load(f)
    print("...loaded model in {:.2f}s".format(time.time()-st))

    FEAS_IN = [fea for fea in MODL.model.hyperparameters['input_features']]
    FEAS_OUT = [fea for fea in MODL.model.hyperparameters['output_features']]
    input_features_desc, output_features_desc = "",""
    for fea in FEAS_IN:
        if fea['type'] == "image":
            input_features_desc += "\t{}\t({}: {})\n".format(fea['name'],fea['type'],"({}, {}) {}".format(fea['width'],fea['height'],chan_count_to_mode(fea['num_channels'])))
        else: input_features_desc += "\t{}\t({})\n".format(fea['name'],fea['type'])
    for fea in FEAS_OUT:
        if fea['type'] == "category":
            fea['meta'] = MMTA[fea['name']]
            output_features_desc += "\t{}\t(category with {} classes)\n".format(fea['name'],fea['num_classes'])
            output_features_desc += "\t\t\t{}\n".format(", ".join(fea['meta']['idx2str']))
        else:
            output_features_desc += "\t{}\t({})\n".format(fea['name'],fea['type'])

    #print(output_features)
    console_msg = """#################### FRESH EYES ####################
I've just loaded a saved model from {0}
To check that the server is working, go to http://localhost:{1}/
It looks like the model I loaded requires the following inputs to make a prediction:
{2}
Make note of these names, as these particular fields will be required by API calls.
It looks like the following values will result from a prediction.
{3}
Make note of these as well, as these fields will be returned to API calls.
Invoke Cntl+C to stop the server
#################### FRESH EYES ####################
"""
    print(console_msg.format(pth_mdl,config['port_num'],input_features_desc, output_features_desc))


###############################################################
##                                                           ##
##                          flask                            ##
##                                                           ##
###############################################################


@app.route('/')
def root():
    return 'Fresh Eyes says hello!\n{}\n'.format(FEAS_IN, FEAS_OUT)


@app.route('/predict', methods=['POST'])
def predict():
    print('## PREDICT')
    st = time.time()
    post_data = request.json
    if post_data is None:
        return "please provide POST data", 500

    # process any images that were passed
    # convert from base64 strings to PIL images, save to local temp directory
    tmp_imgs = []
    for fea in FEAS_IN:
        if fea['type'] == "image":
            w,h,mode = fea['width'],fea['height'],chan_count_to_mode(fea['num_channels'])
            if fea['name'] not in post_data: return "I expected an image '{}' ({}x{} {}) as an input, but I did not find any such image in the post data.".format(fea['name'],w,h,mode), 500
            #TODO: resize any images to match expected dimension
            im = req_string_to_image(post_data[fea['name']])
            #print("I need an image of ({}, {}) {} and found an image of {} {}".format(w,h,mode,im.size, im.mode))
            if im.mode != mode:
                print("converting this image from {} to {}. this slows things down a bit, consider converting in advance.".format(im.mode,mode))
                im = im.convert(mode)

            if im.size != (w,h):
                print("resizing this image from {} to ({}, {}). this slows things down a bit, consider resizing in advance.".format(im.size,w,h))
                im = im.resize((w,h))

            #im.show()
            pth_im = save_temp_image(im)
            tmp_imgs.append(pth_im)
            post_data[fea['name']] = pth_im


    data_dict = {k:[v] for (k,v) in post_data.items()} # even though we're making just one prediction, the dict needs to hold lists
    prediction = do_predict(MODL, data_dict)
    shutil.rmtree(PTH_TMP)

    #print(prediction)
    response = {}
    for fea in FEAS_OUT:
        resp_fea = {}
        if fea['name'] not in prediction:
            print("I expected to find a feature named {} in the prediction, but did not.".format(fea['name']))
            continue

        if fea['type'] == "category":
            resp_fea['prediction'] = prediction[fea['name']]['predictions'][0]
            resp_fea['probability'] = prediction[fea['name']]['probability'].tolist()[0]

            #resp_fea['probabilities'] = prediction[fea['name']]['probabilities'].tolist()[0]
            #resp_fea['probabilities'] = [round(n,6) for n in resp_fea['probabilities']]

            resp_fea['probabilities'] = {}
            for idx,val in enumerate(prediction[fea['name']]['probabilities'].tolist()[0]):
                category_name = fea['meta']['idx2str'][idx]
                resp_fea['probabilities'][category_name] = round(val,ROUND_FLOATS_TO)
        
        if fea['type'] == "numerical":
            # ksteinfe: SUPER FUCKING HACKY
            print(prediction)
            resp_fea = float(prediction['label']['predictions'][0])

        else:
            print("I don't know how to handle features of type {}, so cannot process the feature named {}".format(fea['type'],fea['name']))
            continue

        response[fea['name']] = resp_fea

    print("## prediction completed in {:.2f}s\n".format(time.time()-st))
    return json.dumps(response)

@app.errorhandler(404)
def not_found(error):
    return 'This endpoint does not exist', 404

@app.errorhandler(500)
def other_errors(error):
    return 'Something went wrong. \n\n {}'.format(error), 500


###############################################################
##                                                           ##
##                          util                             ##
##                                                           ##
###############################################################

def save_temp_image(im):
    #TODO: is the PNG format an issue here?
    if not os.path.exists(PTH_TMP): os.makedirs(PTH_TMP)

    pth_im = os.path.join(PTH_TMP,"{}.png".format(str(uuid.uuid4())))
    im.save(pth_im)
    return(pth_im)

def req_string_to_image(s):
    data = base64.decodestring(bytes(s, 'utf-8'))
    im = Image.open(io.BytesIO(data))
    return im

def chan_count_to_mode(nc):
    if nc==1: return "L"
    if nc==3: return "RGB"
    if nc==4: return "RGBA"
    print("Encountered an unexpected number of channels ({})".format(nc))
    return False

def do_predict(mdl, data_dict):
    # obtain predictions
    #print("getting prediction for {}".format(data_dict))
    st = time.time()
    predictions = mdl.predict(
        data_dict=data_dict,
        return_type='dict',
        batch_size=128,
        gpus=None,
        gpu_fraction=1,
        logging_level=logging.ERROR
    )
    #print("I made a prediction in {:.2f}s".format(time.time()-st))
    return predictions


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')
    if not 'pth_mdls' in config['DEFAULT'] or not 'port_num' in config['DEFAULT']  or not 'model_to_load' in config['DEFAULT']:
        raise Exception("Configuration error. Please create a configuration file as described in README.md")

    if not os.path.isdir(config['DEFAULT']['pth_mdls']):
        raise Exception("The models directory defined in configuration file is not actually a directory: {}".format(config['DEFAULT']['pth_mdls']))
    else:
        config['DEFAULT']['pth_mdls'] = os.path.abspath(os.path.realpath(os.path.expanduser(config['DEFAULT']['pth_mdls'])))

    initialize(config['DEFAULT'])
    app.run(
        # processes=2,
        port=int(config['DEFAULT']['port_num']),
        # host='0.0.0.0',
        # ssl_context=context
        # threaded=True
    )
