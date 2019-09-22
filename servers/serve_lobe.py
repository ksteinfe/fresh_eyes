import os, time, json, operator, logging
import fresh_eyes_server as fe
import numpy as np
from flask import request
from PIL import Image
from tensorflow.python.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.python.keras.preprocessing import image
import os, glob, io
import base64

print("...importing Tensorflow")
import tensorflow as tf


MODL = False
META = False
RESNET50 = False
SAVED_MODEL_NAME = "saved_model.h5"
SAVED_META_NAME = "meta.json"
SHAPE = (224, 224)

def initialize(cfg):
    pth_mdl = os.path.join( cfg['pth_mdls'], cfg['model_to_load'], SAVED_MODEL_NAME)
    pth_mta = os.path.join( cfg['pth_mdls'], cfg['model_to_load'], SAVED_META_NAME)
    if not os.path.isfile(pth_mdl): raise Exception("Could not find the model specified: {}".format(pth_mdl))
    if not os.path.isfile(pth_mta): raise Exception("Could not find the meta file specified: {}".format(pth_mta))

    global META
    with open(pth_mta) as f: META = json.load(f)

    global resnet50
    print("\nloading ResNet50... this could take a bit of time. I'll let you know when I'm done.\n")
    st = time.time()
    resnet50 = fe.util.get_resnet50(shape=SHAPE + (3,))
    #bottleneck_train_features = resnet50.predict(input_train)
    #bottleneck_test_features = resnet50.predict(input_test)
    print("\nCompleted loading ResNet50 in {0:.2f}s \n".format(time.time() - st))

    global MODL
    # load a model
    st = time.time()
    print("...loading model from {}".format(pth_mdl))
    MODL = tf.keras.models.load_model(
        pth_mdl,
        custom_objects=None,
        compile=True
    )
    print("...loaded model in {:.2f}s".format(time.time()-st))

    '''
    feed_tensor_keys_string = ""
    for key in MODL._feed_tensors.keys():
        feed_tensor_keys_string += "\t{}\n".format(key)

    print(console_msg.format(exported_path, feed_tensor_keys_string))
    '''

    input_features_desc = False
    output_features_desc = ",".join(META['classes'])
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
    print(console_msg.format(pth_mdl,cfg['port_num'],input_features_desc, output_features_desc))


@fe.app.route('/predict', methods=['POST'])
def predict():
    pdict = fe.serve.pre_predict()
    post_data = request.json
    if not fe.serve.check_post_data(post_data): return "please provide valid POST data", 500
    ## ---------- ##

    ## DO PREDICTION
    pred_data = fe.serve.post_to_pred_simple(post_data)
    #print(pred_data)
    prediction = do_predict(MODL, pred_data)
    if not prediction: return "prediction failed. maybe try again? it could work next time.", 500
    fe.util.clear_temp_path()

    ## FORMAT RESPONSE
    response = do_format_response(prediction)

    ## ---------- ##
    fe.serve.post_predict(pdict)
    return json.dumps(response)


def resize(arr, shape):
    return np.array(Image.fromarray(arr).resize(shape))

def decode_img(msg):
#     msg = msg[msg.find(b"<plain_txt_msg:img>")+len(b"<plain_txt_msg:img>"):
#               msg.find(b"<!plain_txt_msg>")]
    msg = base64.b64decode(msg)
    buf = io.BytesIO(msg)
    img = Image.open(buf)
    return img

def preprocess(arr, shape=(224, 224)):
    arr = np.array([resize(arr[i], shape) for i in range(0, len(arr))]).astype('float32')
    arr = preprocess_input(arr)
    return arr

def do_predict(model, pred_data):
    # obtain predictions
    #print("getting prediction for {}".format(pred_data))
    #st = time.time()
    try:
        image_path = pred_data['image_path']
        im = Image.open(image_path)

        # adam decodes base64, we dont
        # img = decode_img(im).resize((224,224)).convert('RGB')
        # we dont
        img = im.resize((224,224)).convert('RGB')
        img = image.img_to_array(img)
        x = preprocess_input(img)
        pred = model.predict(resnet50.predict(np.array([x])))[0]
        pred = [str(f) for f in pred]


        prediction = list(zip(pred, META['classes']))
        prediction = pred
        #print(prediction)
        return prediction

        '''
        predictions = predictor(
            {
                "image_bytes": [base64.decodestring(bytes(pred_data['image'], 'utf-8'))],
                "batch_size": 1
            }
        )
        '''
    except Exception as e:
        print("!!!!!!!!!! PREDICTION FAILED !!!!!!!!!!")
        print(e)
        return False

    #print("I made a prediction in {:.2f}s".format(time.time()-st))
    return predictions

def do_format_response(prediction):
    # TODO: return prediction and probability
    # TODO: sort probabilities such that most probable is at top
    # response['prediction']
    # response['probability']

    response = {}
    #response = {'this_method':'is not finished yet.'}
    #response = prediction

    response['probabilities'] = {}
    for cls, prob in zip(META['classes'],prediction):
        response['probabilities'][cls] = prob

    return response


if __name__ == '__main__':
    cfg = fe.util.load_config('LOBE')
    initialize(cfg)
    fe.app.run(
        # processes=2,
        port= int(cfg['port_num']),
        # host='0.0.0.0',
        # ssl_context=context,
        debug=False,
        threaded=False
    )
