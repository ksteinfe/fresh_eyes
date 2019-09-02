import os, time, json, operator, logging
import fresh_eyes_server as fe
import numpy as np
from flask import request

print("...importing Ludwig")
from ludwig.api import LudwigModel

ROUND_FLOATS_TO = 10

MODL, MMTA, FEAS_IN, FEAS_OUT = False, False, False, False


def initialize(cfg):
    pth_mdl = os.path.join( cfg['pth_mdls'], cfg['model_to_load'], "model")
    if not os.path.isdir(pth_mdl):
        raise Exception("Could not find the model specified in the models directory: {}".format(pth_mdl))


    global MODL, MMTA, FEAS_IN, FEAS_OUT
    # load a model
    st = time.time()
    print("...loading model from {}".format(pth_mdl))
    MODL = LudwigModel.load(pth_mdl)
    MODL.set_logging_level(logging.ERROR)
    with open(os.path.join(pth_mdl,"train_set_metadata.json")) as f: MMTA = json.load(f)
    print("...loaded model in {:.2f}s".format(time.time()-st))

    FEAS_IN = [fea for fea in MODL.model.hyperparameters['input_features']]
    FEAS_OUT = [fea for fea in MODL.model.hyperparameters['output_features']]
    input_features_desc, output_features_desc = "",""
    for fea in FEAS_IN:
        if fea['type'] == "image":
            input_features_desc += "\t{}\t({}: {})\n".format(fea['name'],fea['type'],"({}, {}) {}".format(fea['width'],fea['height'],fe.util.chan_count_to_mode(fea['num_channels'])))
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
    print(console_msg.format(pth_mdl,cfg['port_num'],input_features_desc, output_features_desc))


@fe.app.route('/predict', methods=['POST'])
def predict():
    pdict = fe.serve.pre_predict()
    post_data = request.json
    if not fe.serve.check_post_data(post_data): return "please provide valid POST data", 500
    ## ---------- ##

    ## DO PREDICTION
    pred_data = fe.serve.post_to_pred_template(post_data, FEAS_IN)
    #print(pred_data)
    prediction = do_predict(MODL, pred_data)
    if not prediction: return "prediction failed. maybe try again? it could work next time.", 500
    fe.util.clear_temp_path()

    ## FORMAT RESPONSE
    response = do_format_response(prediction)

    ## ---------- ##
    fe.serve.post_predict(pdict)
    return json.dumps(response)


def do_predict(mdl, pred_data):
    # obtain predictions
    #print("getting prediction for {}".format(pred_data))
    #st = time.time()
    try:
        predictions = mdl.predict(
            data_dict=pred_data,
            return_type='dict',
            batch_size=128,
            gpus=None,
            gpu_fraction=1
        )
    except Exception as e:
        print("!!!!!!!!!! PREDICTION FAILED !!!!!!!!!!")
        print(e)
        return False
    #print("I made a prediction in {:.2f}s".format(time.time()-st))
    return predictions

def do_format_response(prediction):
    response = {}
    for fea in FEAS_OUT:
        print("working out a response for feature {}".format(fea['name']))
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

        elif fea['type'] == "numerical":
            # ksteinfe: SUPER FUCKING HACKY
            # print(prediction)
            resp_fea = float(prediction[fea['name']]['predictions'][0])

        else:
            print("I don't know how to handle features of type {}, so cannot process the feature named {}".format(fea['type'],fea['name']))
            continue

        response[fea['name']] = resp_fea

    return response


if __name__ == '__main__':
    cfg = fe.util.load_config('LUDWIG')
    initialize(cfg)
    fe.app.run(
        # processes=2,
        port= int(cfg['port_num']),
        # host='0.0.0.0',
        # ssl_context=context,
        debug=False,
        threaded=False
    )
