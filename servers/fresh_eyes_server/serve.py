import time
from .util import *

print("...importing flask")
from flask import Flask
from flask import request
from collections import OrderedDict
from flask_cors import CORS

app = Flask("Keras ResNet50 API")
CORS(app)


@app.route('/')
def root():
    return 'The Fresh Eyes Server says hello!'


@app.errorhandler(404)
def not_found(error):
    return 'This endpoint does not exist', 404

@app.errorhandler(500)
def other_errors(error):
    return 'Something went wrong. \n\n {}'.format(error), 500

def check_post_data(post_data):
    if post_data is None: return False
    return True

def pre_predict():
    print('## PREDICT')
    pdict = {"start_time":time.time()}
    return pdict

def post_predict(pdict):
    print("prediction completed in {:.2f}s\n".format(time.time()-pdict['start_time']))

# simple conversion of POST data to dictionary of data ready for a prediction
def post_to_pred_simple(post_data, accept_non_images=False, enforced_image_size=False):
    # process any images that were passed
    # convert from base64 strings to PIL images, save to local temp directory
    for key in post_data:
        print(key)

    data_dict = {}
    for key in post_data:
        #TODO: this assumes all keys are base64 images... what if they're not?
        im = req_string_to_image(post_data[key])
        if not im:
            if accept_non_images:
                # if accepting non-images, we'll take this data as-is
                data_dict[key] = post_data[key]
            else:
                print("!!! What's this!? The given data at key '{}' doesn't look like a base 64 image.".format(key))
            continue

        if enforced_image_size:
            if im.size != enforced_image_size:
                print("resizing this image from {} to ({}, {}). this slows things down a bit, consider resizing in advance.".format(im.size,enforced_image_size[0],enforced_image_size[1]))
                im = im.resize(enforced_image_size)

        #im.show()
        pth_im = save_temp_image(im)
        data_dict[key] = pth_im

    return data_dict

def post_to_pred_template(post_data, ludwig_model_input_features):
    # process any images that were passed
    # convert from base64 strings to PIL images, save to local temp directory
    pred_data = {}
    for fea in ludwig_model_input_features:
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

            pth_im = save_temp_image(im)
            post_data[fea['name']] = pth_im

        pred_data[fea['name']] = [ post_data[fea['name']] ] # even though we're making just one prediction, the dict needs to hold lists

    #pred_data = {k:[v] for (k,v) in post_data.items()} # even though we're making just one prediction, the dict needs to hold lists
    return pred_data
