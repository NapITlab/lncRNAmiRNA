import os

import numpy as np
from django.conf import settings
from keras import models


dict_n = {'A': 0, 'T': 1, 'C': 2, 'G': 3}
change = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C', '_': '_'}


def generator_test(data, batch_size):
    i = 0
    while True:
        image1 = np.zeros((batch_size, 23, 4))
        image2 = np.zeros((batch_size, 5000, 4))
        target = np.zeros((batch_size, 1))
        for k in range(batch_size):
            example = data.iloc[i]
            lncrna = example['read']
            mirna = example['seq']

            mirna = mirna.replace('U', 'T')
            mirna = mirna[::-1]
            mirna = ''.join([change[i] for i in mirna])
            lncrna = lncrna.replace('U', 'T')

            if len(lncrna) <= 5000:
                for j in range(len(mirna)):
                    Nucl = dict_n[mirna[j]]
                    image1[k, j, Nucl] = 1

                for j in range(len(lncrna)):
                    Nucl = dict_n[lncrna[j]]
                    image2[k, j, Nucl] = 1
            target[k] = example['target']
            i += 1
            if i >= len(data):
                i = 0
        yield [image1, image2], target


class ModelGetter(object):
    _model = None

    @property
    def model(self):
        if self._model is None:
            self._model = models.load_model(
                os.path.join(
                    settings.PATH_TO_DATA_FOR_MODEL,  "best4.h5"))
        return self._model


model_getter = ModelGetter()


def run_predict(data, batch_size):

    batch_num = data.shape[0]//batch_size + int(data.shape[0] % batch_size != 0)
    pred_all = []
    y_all = []
    k = 0
    for batch in generator_test(data, batch_size):
        pred = model_getter.model.predict(batch[0])
        y = batch[1]
        pred_all = pred_all + list(pred)
        y_all = y_all + list(y)

        k += 1
        if k == batch_num:
            break
    # pred_all
    # y_all
    return pred_all


def predict_one(data):
    return run_predict(data, batch_size=1)


def run_val(data):
    return run_predict(data, batch_size=4)
