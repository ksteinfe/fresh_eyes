import os, time, json, operator, logging
import fresh_eyes_server as fe
import numpy as np
from flask import request

print("...importing Tensorflow")
import tensorflow as tf


PRED = False


def initialize(cfg):
    pth_mdl = os.path.join( cfg['pth_mdls'], cfg['model_to_load'])
    if not os.path.isdir(pth_mdl):
        raise Exception("Could not find the model specified in the models directory: {}".format(pth_mdl))


    global PRED
    # load a model
    st = time.time()
    print("...loading model from {}".format(pth_mdl))

    PRED = tf.contrib.predictor.from_saved_model(pth_mdl)
    print("...loaded model in {:.2f}s".format(time.time()-st))

    feed_tensor_keys_string = ""
    for key in PRED._feed_tensors.keys():
        feed_tensor_keys_string += "\t{}\n".format(key)

    print(console_msg.format(exported_path, feed_tensor_keys_string))

    input_features_desc = False
    output_features_desc = False
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
    prediction = do_predict(PRED, pred_data)
    if not prediction: return "prediction failed. maybe try again? it could work next time.", 500
    fe.util.clear_temp_path()

    ## FORMAT RESPONSE
    response = do_format_response(prediction)

    ## ---------- ##
    fe.serve.post_predict(pdict)
    return json.dumps(response)


def do_predict(predictor, pred_data):
    # obtain predictions
    #print("getting prediction for {}".format(pred_data))
    #st = time.time()
    print("this isn't going to work becuase pred_data['image'] might not exist, and even if it does, we are providing a reference to a local temp image and not an image string.")
    try:
        predictions = predictor(
            {
                "image_bytes": [base64.decodestring(bytes(pred_data['image'], 'utf-8'))],
                "batch_size": 1
            }
        )
    except Exception as e:
        print("!!!!!!!!!! PREDICTION FAILED !!!!!!!!!!")
        print(e)
        return False
    #print("I made a prediction in {:.2f}s".format(time.time()-st))
    return predictions

def do_format_response(prediction):
    response = {'this_method':'is not finished yet.'}
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
