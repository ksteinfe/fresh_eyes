import os, glob, io, base64, shutil, json
import fresh_eyes_trainer as fe

from tensorflow.python.keras import backend as K
from tensorflow.python.keras.layers import Conv2D, GlobalAveragePooling2D, Input, Dropout, Dense
from tensorflow.python.keras.utils import to_categorical
from tensorflow.python.keras.models import Model
from tensorflow.python.keras.callbacks import Callback, TensorBoard
from tensorflow.python.keras.backend import set_session
from tensorflow.python.keras.models import load_model
import tensorflow as tf

from collections import defaultdict
from matplotlib.pyplot import imshow
from PIL import Image
import datetime, time
import numpy as np


asci_eye = "\n========== (o_o) Fresh Eyes ==========\n{}"

SAVED_MODEL_NAME = "saved_model.h5"
SAVED_META_NAME = "meta.json"

def main(cfg):
    print("Training has Started!")
    sess = tf.Session()
    graph = tf.get_default_graph()
    set_session(sess)

    #print(sess)

    batch_size = 32
    test_train_split = cfg['test_train_split']
    max_epoch = cfg['epochs']
    shape = (224, 224)
    #dropout_prob = 0.3
    #train_size_per_label = 500
    #test_size_per_label = 100
    meta = {}
    meta['img_fmt'] = cfg['image_extension']
    meta['shape'] = shape

    input_train, input_test, out_train, out_test, classes = fe.util.get_local_images(cfg['pth_data'], test_train_split, meta['img_fmt'], shape)
    meta['classes'] = classes
    print("input_test shape: {}".format(input_test.shape))

    x = fe.util.get_cifar10()
    print("cifar10 shape: {}".format(x[0].shape))

    total_train_steps = len(input_train) // batch_size
    out_train = to_categorical(out_train, len(classes))
    out_test = to_categorical(out_test, len(classes))

    print("\nloading ResNet50... this could take a bit of time. I'll let you know when I'm done.\n")
    st = time.time()
    resnet50 = fe.util.get_resnet50(shape=shape + (3,))
    bottleneck_train_features = resnet50.predict(input_train)
    bottleneck_test_features = resnet50.predict(input_test)
    print("\nCompleted loading ResNet50 in {0:.2f}s \n".format(time.time() - st))

    in_layer = Input(shape=(bottleneck_train_features.shape[1:]))
    x = Conv2D(filters=100, kernel_size=2)(in_layer)
    x = Dropout(0.4)(x)
    x = GlobalAveragePooling2D()(x)
    x = Dropout(0.3)(x)
    predictions = Dense(len(classes), activation='softmax')(x)
    model = Model(inputs=in_layer, outputs=predictions)
    print(model.summary())

    def save_model(cfg, epoch):
        pth_save = os.path.join(cfg['pth_model_save'],"{}-{:05d}".format(cfg['data_to_train_on'],epoch))
        print("saving model to {}".format(pth_save))
        if not os.path.exists('my_folder'): os.makedirs(pth_save)
        pth_modl = os.path.join(pth_save,SAVED_MODEL_NAME)
        tf.keras.models.save_model(
            model,
            pth_modl,
            overwrite=True,
            include_optimizer=True,
            save_format=None
        )
        pth_meta = os.path.join(pth_save,SAVED_META_NAME)
        with open(pth_meta, "w") as write_file: json.dump(meta, write_file)

    class RecordAccuracy(Callback):
        def on_epoch_begin(self, epoch, logs=None):
            print(f'Running epoch {epoch}. Total {total_train_steps} batches')
        def on_batch_end(self, batch, logs=None):
            loss = logs['loss']
            if not batch % 10:
                print(f'Running batch {batch}: train loss - {loss}')
        def on_epoch_end(self, epoch, logs=None):
            loss = logs["loss"]
            val_acc = logs["val_acc"]
            print(f'Epoch {epoch}: train loss - {loss}. test accuracy - {val_acc}')
            save_model(cfg, epoch)

    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['acc'])
    model.fit_generator(batch_generator(bottleneck_train_features, out_train),
                        steps_per_epoch=len(bottleneck_train_features) // batch_size,
                          validation_data=(bottleneck_test_features, out_test),
                          verbose=2,
                          epochs=max_epoch,
                          callbacks=[RecordAccuracy(), TensorBoard()])

    print(asci_eye.format("Training Complete!"))
    save_model(cfg, max_epoch)






def batch_generator(x, y, batch_size=32):
    while True:
        for step in range(len(x) // batch_size):
            yield x[step*batch_size:(step+1)*batch_size, ...], y[step*batch_size:(step+1)*batch_size, ...]


if __name__ == '__main__':
    print(asci_eye.format("This script performs transfer learning of a given set of images using ResNet50.\nTraining images will be resized to 224px square."))
    cfg = fe.util.load_config('LOBE')

    print("Models will be saved to the following location. Any existing models found there will be deleted.\n'{}'\n".format(cfg['pth_model_save']))

    try:
       if os.path.isdir(cfg['pth_model_save']):
           if input("EXISTING SAVED MODELS FOUND.\nAll models at {} will be deleted.\nAre you sure? (y/n)".format(cfg['pth_model_save'])) != "y": exit()
           shutil.rmtree(cfg['pth_model_save'])
    except Exception as e:
       print('Error while deleting model save directory: {}'.format(cfg['pth_model_save']))
       print(e)
       exit()

    main(cfg)
