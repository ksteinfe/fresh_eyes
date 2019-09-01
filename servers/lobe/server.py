MODEL_TO_LOAD = "_sample_a"

import tensorflow as tf
import numpy as np
import os
import base64

from flask import Flask
from flask import request
from collections import OrderedDict
from flask_cors import CORS
app = Flask("LobeAPI")
CORS(app)

# general
import yaml, logging, json, os, time
from functools import partial
from threading import RLock

dir_path = os.path.dirname("./")
exported_path = os.path.join(dir_path, "saved_models", MODEL_TO_LOAD)


###############################################################
##                                                           ##
##                          debugging                        ##
##                                                           ##
###############################################################

base64String = "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgKCgkICQkKDA8MCgsOCwkJDRENDg8QEBEQCgwSExIQEw8QEBD/2wBDAQMDAwQDBAgEBAgQCwkLEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBD/wAARCAA8ADwDASIAAhEBAxEB/8QAHgAAAQQDAAMAAAAAAAAAAAAAAAQFBgcBCAkCAwr/xAA+EAABAgMEBQcHDQEAAAAAAAABAAIDBBEFBhNRBxIUFSExQVKRoeHwCAkiYXGksRcYMkNTVmJygaLB0dLT/8QAFAEBAAAAAAAAAAAAAAAAAAAAAP/EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAMAwEAAhEDEQA/ANGMM5Iwzknbd78vHWjd78vHWgacM5Iwzknbd78vHWvW+BDhu1XvofYgbcM5IwzknVkliDWYahZ3e/Lx1oGnDOSMM5J23e/Lx1o3e/Lx1oLRlrlOnCRLenQVPN8XJR8nc79l+4f6Wy/kFXQu7fnSpbFk3ns/bJWDd2PMMh4r4dIgmZZoNWOaeR7uFacVvd83vRH90/f5r/og4vXwu1MXcsjborNUPiCEDUHiQTmclVE1OOMUmvOuofnMdF1xrj6BLGta7FibHNRb1y0u+JtMaJWGZObcRR7yOVjeNK8FytmXHEKCTXdnKzLGu4gmhU1iQpRkTU1K+upVcWA87UwesKdR3ux/aUEjs+7MO0YRiQD9EVcMh+pXk67Eu00dF4j8J/tLrpxHCVj8fq/5WI0V2IUF8eRzpouToZ0qutu+U9s1lWnZcxZsxN4UZ+y1cyM1+pDY9z6vgth0AFMTWrRtD1VXzy78i9Ls7kb8i9Ls7kHU3zrDC/ydLDA5r4Sh9ynVyDmYJxCpa+2HRGFjzVp5R4CaY8CDEfrB3L6igxd6ATNQxTnCnkeUdjnhzqHSUaHJHWYau5il2/IvS7O5BZt3piTkYERszF1S9tB6JPwRFjSbnktjcPylVlvyL0uzuRvyL0uzuQRfaCjaCk9SipQKNoKNoKT1KKlAo2go2gpPUoqUCjaCjaCk9SipQf/Z"

predictor = tf.contrib.predictor.from_saved_model(exported_path)
# how to see what inputs are required by the model

console_msg = """#################### FRESH EYES ####################
Hello from the server.py file!
I've just loaded a saved Tensorflow model from {0}
This model requires the following inputs to make a prediction. Note that some, but not all of these fields will be required by API calls.
{1}
#################### FRESH EYES ####################
"""
feed_tensor_keys_string = ""
for key in predictor._feed_tensors.keys():
    feed_tensor_keys_string += "\t{}\n".format(key)

print(console_msg.format(exported_path, feed_tensor_keys_string))

# Prove it works:
# print(predictor({"image_bytes": [base64.decodestring(bytes(base64String, 'utf-8'))], "batch_size": 1}))



###############################################################
##                                                           ##
##                          helpers                          ##
##                                                           ##
###############################################################

def get_lists(output):
    lists = set()
    for k in output.keys():
        if 'idx' in k and '_' in k:
            lists.add(k.split('_')[0])
    return lists

def correct_lists(output):
    final_dict = {}
    lists = get_lists(output)
    # Good idea: (need to test)
    ordered_output = OrderedDict(sorted(output.items(), key=lambda t: t[0]))
    if len(lists) > 0:
        for current_label in lists:
            for k in ordered_output.keys():
                if '_' in k and 'idx' in k and k.split('_')[0] == current_label:
                    final_dict[current_label] = final_dict.get(current_label, list())
                    final_dict[current_label].append(ordered_output[k])
                elif '_' in k and 'idx' in k and k.split('_')[0] != current_label:
                    pass
                else:
                    final_dict[k] = ordered_output[k]
    else:
        final_dict = output
    return final_dict


###############################################################
##                                                           ##
##                          flask                            ##
##                                                           ##
###############################################################


@app.route('/')
def root():
    return 'Lobe says hello!\n'

@app.route('/predict', methods=['POST'])
def predict():
    print('/predict')
    data = request.json

    if 'numbers' in data:
        lhs = predictor({"numbers": [data['numbers']],"image_bytes": [base64.decodestring(bytes(data['image'], 'utf-8'))], "batch_size": 1})
    else:
        lhs = predictor({"image_bytes": [base64.decodestring(bytes(data['image'], 'utf-8'))], "batch_size": 1})

    lhs = {k: v if type(v) is not np.ndarray else v.tolist() for k, v in lhs.items()}
    for k, v in lhs.items():
        print('*' * 80)
        print(v)
        print(type(v) is list)
        if type(v) is list and type(v[0]) is bytes:
            lhs[k] = [x.decode('UTF-8') for x in v]
        if type(v) is list and type(v[0]) is list and type(v[0][0]) is bytes:
            lhs[k] = [[y.decode('UTF-8') for y in x] for x in v][0]
        elif type(v) is list and type(v[0]) is list and type(v[0][0]) is float:
            lhs[k] = v[0]
    lhs = correct_lists(lhs)
    for k, v in lhs.items():
        # if it's a list of lists
        if type(v) is list and type(v[0]) is list:
            print(v)
            lhs[k] = list(zip(*v))
    # return json.dumps({"outputs": lhs})
    return json.dumps(lhs)

@app.errorhandler(404)
def not_found(error):
    return 'This endpoint does not exist', 404

@app.errorhandler(500)
def other_errors(error):
    return 'Something went wrong. \n\n {}'.format(error), 500

if __name__ == '__main__':
    app.run(
        # processes=2,
        port=5008,
        # host='0.0.0.0',
        # ssl_context=context
        # threaded=True
    )
