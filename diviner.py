#!/usr/bin/python3
# Seed value
# Apparently you may use different seed values at each stage
seed_value= 3

# 1. Set `PYTHONHASHSEED` environment variable at a fixed value
import os
os.environ['PYTHONHASHSEED']=str(seed_value)

# 2. Set `python` built-in pseudo-random generator at a fixed value
import random
random.seed(seed_value)

# 3. Set `numpy` pseudo-random generator at a fixed value
import numpy as np
np.random.seed(seed_value)

# 4. Set the `tensorflow` pseudo-random generator at a fixed value
import tensorflow as tf
#tf.random.set_seed(seed_value)
# for later versions:
tf.compat.v1.set_random_seed(seed_value)

# 5. Configure a new global `tensorflow` session
from keras import backend as K
session_conf = tf.ConfigProto(intra_op_parallelism_threads=1, inter_op_parallelism_threads=1)
sess = tf.Session(graph=tf.get_default_graph(), config=session_conf)
K.set_session(sess)
# for later versions:
# session_conf = tf.compat.v1.ConfigProto(intra_op_parallelism_threads=1, inter_op_parallelism_threads=1)
# sess = tf.compat.v1.Session(graph=tf.compat.v1.get_default_graph(), config=session_conf)
# tf.compat.v1.keras.backend.set_session(sess)

from datetime import date
import numpy as np
import matplotlib.pyplot as plt

import data_reader
import predictor
import prediction_quality

print('Hello mister! I\'m your diviner')

#list of countries
countries = data_reader.european_countries()

#analysed dates
START_DATE  = date(2020, 2, 1)
END_DATE    = date(2020, 5, 26)

# Model parameters
N_STEPS_BACKWARDS   = 7
N_STEPS_FORWARD     = 7
N_FEATURES          = 6
N_NEURONS           = 32

# Choose model
model = 'neural_network'
#model = 'linear'

date_list   = data_reader.date_set_preparation(START_DATE, END_DATE)

(cases_c, cases_d, cases_r) = data_reader.read_covid_file(countries, date_list)

# Dataset creation and splitting - all for training set
(X_learn, Y_learn, X_test, Y_test)                              \
    = predictor.create_countries_train_test_set                 \
    (countries, cases_c, cases_d, cases_r, 1, \
    N_STEPS_BACKWARDS, N_STEPS_FORWARD)

if (model == 'neural_network'):
    # Model creation and training
    model = predictor.lstm_model_create(N_NEURONS, N_STEPS_BACKWARDS, N_FEATURES, N_STEPS_FORWARD)
    model.fit(X_learn, Y_learn, epochs=200, verbose=1)

# Create set for prediction for future only
X_predict = predictor.create_countries_predition_set            \
    (countries, cases_c, cases_d, cases_r, N_STEPS_BACKWARDS)

Y_predict   = dict()
acc_predict = dict()
for country in countries:
    print(country)

    # Model prediction for country
    Y_predict[country] = model.predict(X_predict[country], verbose=0)
    # Limit values in prediction
    Y_predict[country] = Y_predict[country].clip(min=0)

    # Translate prediction for absolute value 7 days in future (accumulated)
    acc_predict[country] = predictor.translate_prediction   \
        (X_predict[country], Y_predict[country])

    # Round accumulated prediction
    acc_predict[country] = np.round(acc_predict[country])

    # Calculate prediction for future
    last_value = X_predict[country][0, -1, 3]
    prediction_points = np.zeros(N_STEPS_FORWARD)
    Y_predict[country] = Y_predict[country].flatten()
    for i in range(N_STEPS_FORWARD):
        prediction_points[i] = last_value + Y_predict[country][i]

    # Plot prediction results
    t1 = np.zeros_like(cases_c[country])
    for i in range(len(cases_c[country])):
        t1[i] = i

    t2 = np.zeros(len(Y_predict[country]))
    t2[0] = t1[-1] + 1
    for i in range(len(Y_predict[country])):
        if i != 0:
            t2[i] = t2[i - 1] + 1

    # Plot results
    plt.plot(t1, cases_c[country], 'b.')
    plt.plot(t2, prediction_points, 'r.')
    plt.show()

    print(acc_predict[country])

print("Done!")