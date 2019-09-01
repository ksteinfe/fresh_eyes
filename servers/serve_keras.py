import os, logging, shutil, time, json, configparser, operator
import tempfile, uuid
import io, base64
print("...importing PIL")
from PIL import Image

print("...importing numpy")
import numpy as np

print("...importing flask")
from flask import Flask
from flask import request
from collections import OrderedDict
from flask_cors import CORS

print("...importing keras")
import keras.preprocessing.image
from keras.preprocessing import image
from keras.applications import resnet50, imagenet_utils

ROUND_FLOATS_TO = 10
IMAGE_SIZE=(224, 224)

# images recieved by API calls are saved locally, used for prediction, and then deleted
PTH_TMP = os.path.join(tempfile.gettempdir(),"ludwig_server_temp_images")

###############################################################
##                                                           ##
##                          INIT                             ##
##                                                           ##
###############################################################
MODL = False

app = Flask("Keras ResNet50 API")
CORS(app)

def initialize(config):
    global MODL
    MODL = resnet50.ResNet50() # Load Keras' ResNet50 model that was pre-trained against the ImageNet database
    #print(output_features)
    console_msg = """#################### FRESH EYES ####################
I've just loaded the ResNet50 Keras Model pre-trained on the ImageNet database
To check that the server is working, go to http://localhost:{0}/
Invoke Cntl+C to stop the server
#################### FRESH EYES ####################
"""
    print(console_msg.format(config['port_num']))


###############################################################
##                                                           ##
##                          flask                            ##
##                                                           ##
###############################################################


@app.route('/')
def root():
    return 'Fresh Eyes says hello!'


@app.route('/predict', methods=['POST'])
def predict():
    print('## PREDICT')
    st = time.time()
    post_data = request.json
    if post_data is None:
        return "please provide POST data", 500

    # process any images that were passed
    # convert from base64 strings to PIL images, save to local temp directory
    for key in post_data:
        print(key)

    data_dict = {}
    for key in post_data:
        #TODO: resize any images to match expected dimension
        im = req_string_to_image(post_data[key])
        if not im:
            print("!!! What's this!? The given data at key {} doesn't look like a base 64 image.".format(key))
            continue

        if im.size != IMAGE_SIZE:
            print("resizing this image from {} to ({}, {}). this slows things down a bit, consider resizing in advance.".format(im.size,IMAGE_SIZE[0],IMAGE_SIZE[1]))
            im = im.resize(IMAGE_SIZE)

        #im.show()
        pth_im = save_temp_image(im)
        data_dict[key] = pth_im


    prediction = do_predict(MODL, data_dict)
    shutil.rmtree(PTH_TMP)

    response = prediction

    for k in response:
        best = max(response[k].items(), key=operator.itemgetter(1))
        print("{} looks {:.2%} like a {}".format(k,best[1]/100,best[0]))

    print("## prediction completed in {:.2f}s\n".format(time.time()-st))
    return json.dumps(response)

@app.errorhandler(404)
def not_found(error):
    return 'This endpoint does not exist', 404

@app.errorhandler(500)
def other_errors(error):
    return 'Something went wrong. \n\n {}'.format(error), 500



def do_predict(mdl, data_dict):
    # obtain predictions
    #print("getting prediction for {} images".format(len(data_dict)))
    #st = time.time()
    keys = data_dict.keys()
    pth_imgs = [data_dict[k] for k in keys]

    arr_imgs = []
    for pth_img in pth_imgs:
        img = image.load_img(pth_img) # Load the image file, expecting to be 224x224 pixels (required by this model)
        x = image.img_to_array(img) # Convert the image to a numpy array
        x = resnet50.preprocess_input(x) # Scale the input image to the range used in the trained network
        arr_imgs.append(x)

    x = np.stack( arr_imgs, axis=0 )
    predictions = mdl.predict(x) # Run the image through the deep neural network to make a prediction
    #print("I made a set of predictions in {:.2f}s".format(time.time()-st))

    decoded_predictions = resnet50.decode_predictions(predictions, top=len(predictions[0]) ) # Look up the names of the predicted classes. Index zero is the results for the first image.
    response = {}
    for key, prediction in zip(keys,decoded_predictions):
        d = {}
        for imagenet_id, name, likelihood in prediction:
            d[name.lower()] = float(round(likelihood,ROUND_FLOATS_TO))
        response[key] = d

    return response



if __name__ == '__main__':
    config = {}
    config['port_num'] = 5008

    initialize(config)
    app.run(
        # processes=2,
        port=int(config['port_num']),
        # host='0.0.0.0',
        # ssl_context=context
        # threaded=True
    )
