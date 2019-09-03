import time, json, operator
import fresh_eyes_server as fe
import numpy as np
from flask import request

print("...importing keras")
import keras.preprocessing.image
from keras.preprocessing import image
from keras.applications import resnet50, imagenet_utils

ROUND_FLOATS_TO = 10
IMAGE_SIZE=(224, 224)

MODL = False


def initialize(cfg):
    global MODL
    MODL = resnet50.ResNet50() # Load Keras' ResNet50 model that was pre-trained against the ImageNet database
    #print(output_features)
    console_msg = """#################### FRESH EYES ####################
I've just loaded the ResNet50 Keras Model pre-trained on the ImageNet database
To check that the server is working, go to http://localhost:{0}/
Invoke Cntl+C to stop the server
#################### FRESH EYES ####################
"""
    print(console_msg.format(cfg['port_num']))


@fe.app.route('/predict', methods=['POST'])
def predict():
    pdict = fe.serve.pre_predict()
    post_data = request.json
    if not fe.serve.check_post_data(post_data): return "please provide valid POST data", 500
    ## ---------- ##

    ## DO PREDICTION
    pred_data = fe.serve.post_to_pred_simple(post_data, accept_non_images=False, enforced_image_size = IMAGE_SIZE)
    prediction = do_predict(MODL, pred_data)
    fe.util.clear_temp_path()

    ## FORMAT RESPONSE
    response = do_format_response(prediction)

    ## ---------- ##
    fe.serve.post_predict(pdict)
    return json.dumps(response)


def do_predict(mdl, pred_data):
    # obtain predictions
    #if len(pred_data)>1: print("getting prediction for {} images".format(len(pred_data)))
    st = time.time()
    keys = pred_data.keys()
    pth_imgs = [pred_data[k] for k in keys]

    arr_imgs = []
    for pth_img in pth_imgs:
        img = image.load_img(pth_img) # Load the image file, expecting to be 224x224 pixels (required by this model)
        x = image.img_to_array(img) # Convert the image to a numpy array
        x = resnet50.preprocess_input(x) # Scale the input image to the range used in the trained network
        arr_imgs.append(x)

    x = np.stack( arr_imgs, axis=0 )
    predictions = mdl.predict(x) # Run the image through the deep neural network to make a prediction
    #if len(pred_data)>1: print("I made a set of predictions in {:.2f}s".format(time.time()-st))

    decoded_predictions = resnet50.decode_predictions(predictions, top=len(predictions[0]) ) # Look up the names of the predicted classes. Index zero is the results for the first image.
    response = {}
    for key, prediction in zip(keys,decoded_predictions):
        d = {}
        for imagenet_id, name, likelihood in prediction:
            d[name.lower()] = float(round(likelihood,ROUND_FLOATS_TO))
        response[key] = d

    return response

def do_format_response(prediction):
    response = prediction
    for k in response:
        best = max(response[k].items(), key=operator.itemgetter(1))
        print("{} looks {:.2%} like a {}".format(k,best[1]/100,best[0]))
    return response

if __name__ == '__main__':
    cfg = fe.util.load_config('KERAS')
    initialize(cfg)
    fe.app.run(
        # processes=2,
        port= int(cfg['port_num']),
        # host='0.0.0.0',
        # ssl_context=context,
        debug=False,
        threaded=False
    )
