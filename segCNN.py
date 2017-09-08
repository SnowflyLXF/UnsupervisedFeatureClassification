# -*- coding: utf-8 -*-
"""
Created on Thu Sep  7 00:47:51 2017

@author: lxf96
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import numpy as np
import load_data

Imgs, labels = load_data.getData()
train_Img = load_data.preprocess(Imgs)

from keras.layers import Input, Dense, Conv2D, MaxPooling2D, UpSampling2D, Flatten, Reshape, Lambda, concatenate, Activation, BatchNormalization
from keras.layers.advanced_activations import LeakyReLU, PReLU
from keras.optimizers import SGD, Adadelta, Adagrad,Adam, rmsprop
from keras import objectives
from keras.callbacks import TensorBoard
from keras import backend as K
from keras.models import Model
from keras.losses import binary_crossentropy
from keras.callbacks import EarlyStopping


batch_size =100
latent_dim = 30
nb_epoch = 50
intermediate_dim =512
original_dim = 64*64
LRelu = LeakyReLU(alpha=0.3)

input_img = Input(shape=(64,64,1))

conv_1 = Conv2D(40, (3, 3), padding='same',kernel_initializer='normal')(input_img)
conv_1 = Activation(LRelu)(conv_1)
conv_1 = BatchNormalization()(conv_1)
maxpool_1 = MaxPooling2D((2, 2),padding='same')(conv_1)

conv_2 = Conv2D(40, (3, 3), padding='same',kernel_initializer='normal')(maxpool_1)
conv_2 = Activation(LRelu)(conv_2)
conv_2 = BatchNormalization()(conv_2)
maxpool_2 = MaxPooling2D((2, 2),  padding='same')(conv_2)

conv_3 = Conv2D(20, (3, 3),padding='same',kernel_initializer='normal')(maxpool_2)
conv_3 = Activation(LRelu)(conv_3)
conv_3 = BatchNormalization()(conv_3)
maxpool_3 = MaxPooling2D((2, 2),  padding='same')(conv_3)

conv_4 = Conv2D(20, (3, 3),padding='same',kernel_initializer='normal')(maxpool_3)
conv_4 = Activation(LRelu)(conv_4)
conv_4 = BatchNormalization()(conv_4)
maxpool_4 = MaxPooling2D((2, 2),  padding='same')(conv_4)

#conv_5 = Conv2D(20, (3, 3), activation='relu', padding='same',kernel_initializer='normal')(maxpool_4)
#maxpool_5 = MaxPooling2D((2, 2),  padding='same')(conv_5)


#x = Conv2D(5, (3, 3), activation='relu', padding='same',kernel_initializer='normal')(x)
#x = MaxPooling2D((2, 2),  padding='same')(x)
'''
visual = Flatten()(maxpool_4)
h_1 = Dense(intermediate_dim, activation='relu')(visual)#relu?
encoded = Dense(latent_dim, activation='tanh')(h_1)# relu?


if USE == 'autoencoder':
    h_3 = Dense(intermediate_dim,activation=LRelu)(encoded)#for AE
    
    
h_4 = Dense(20*4*4,activation=LRelu)(h_3)
h_5 = Reshape((4,4,20))(h_4)
'''

#conv_6 = Conv2D(20, (3, 3), activation='relu', padding='same',kernel_initializer='normal')(h_5)
#upsample_6 = UpSampling2D((2, 2))(conv_6)

#conv_7 = Conv2D(20, (3, 3), activation='relu', padding='same',kernel_initializer='normal')(h_5)
upsample_7 = UpSampling2D((2, 2))(maxpool_4)

conv_8 = Conv2D(20, (3, 3), activation='relu', padding='same',kernel_initializer='normal')(upsample_7)
upsample_8 = UpSampling2D((2, 2))(conv_8)

conv_9 = Conv2D(40, (3, 3), activation='relu', padding='same',kernel_initializer='normal')(upsample_8)
upsample_9 = UpSampling2D((2, 2))(conv_9)

conv_10 = Conv2D(80,  (3, 3), activation='relu',padding='same',kernel_initializer='normal')(upsample_9)
upsample_10 = UpSampling2D((2, 2))(conv_10)

decoded = Conv2D(1, (3, 3), activation='tanh', padding='same')(upsample_10)


EarlyStopping = EarlyStopping(monitor='val_loss', min_delta=0, patience=3, verbose=0, mode='auto')

def ae_loss(x, decoded):  
    xent_loss = original_dim * objectives.mean_squared_error(x,decoded)
    return xent_loss

autoencoder = Model(inputs=input_img, outputs=decoded)
autoencoder.compile(optimizer='rmsprop', loss=ae_loss)

decoded = Conv2D(1, (3, 3), activation='sigmoid', padding='same')(upsample_8)

EarlyStopping = EarlyStopping(monitor='val_loss', min_delta=0, patience=6, verbose=0, mode='auto')

ae1 = Model(inputs=input_img, outputs=decoded)
ae1.compile(optimizer='rmsprop', loss='binary_crossentropy')

ae1.fit((train_Img[:50000], train_Img[:50000]),
        shuffle=True,
        epochs=50,
        batch_size=batch_size,
        )

class point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class pointMap:
    
    def __init__(self, value):
        self.value = value
        self.used = np.ones_like(value)
        self.row = value.shape[0]
        self.col = value.shape[1]
    
    def getValue(self, p1):
        x = int(getattr(p1,'x'))
        y = int(getattr(p1,'y'))
        return self.value[x, y]
    
    def visit(self,x, y):
        if self.used[x, y]:
            self.used[x, y]=0
            return 1
        else:
            return 0
    
    def getCluster(self):
        mark = []
        pend = []
        x = int(self.row/2-1)
        y = int(self.col/2-1)
        p = point(x, y)
        self.used[x,y]=0
        mark.append((x,y))
        pend.append(p)
        
        for p1 in pend:
            x = int(getattr(p1,'x'))
            y = int(getattr(p1,'y'))
            #print(x,y)
            if x>0 and pointMap.visit(self, x-1, y):
                p2 = point(x-1, y)
                if pointMap.getValue(self, p2) == 1:                        
                    mark.append((x-1,y))
                    pend.append(p2)
            if x<self.row-1 and pointMap.visit(self, x+1, y):
                p2 = point(x+1, y)
                if pointMap.getValue(self, p2) == 1:
                    mark.append((x+1,y))
                    pend.append(p2)
            if y>0 and pointMap.visit(self, x, y-1):
                p2 = point(x, y-1)
                if pointMap.getValue(self, p2) == 1:
                    mark.append((x,y-1))
                    pend.append(p2)
            if y<self.col-1 and pointMap.visit(self, x, y+1):
                p2 = point(x, y+1)
                if pointMap.getValue(self, p2) == 1:
                    mark.append((x,y+1))
                    pend.append(p2)
            '''
            if y>0 and x>0 and pointMap.visit(self, x-1, y-1):
                p2 = point(x-1, y-1)
                if pointMap.getValue(self, p2) == 1:
                    mark.append((x-1,y-1))
                    pend.append(p2)
            if x>0 and y<self.col-1 and pointMap.visit(self, x-1, y+1):
                p2 = point(x-1, y+1)
                if pointMap.getValue(self, p2) == 1:                        
                    mark.append((x-1,y+1))
                    pend.append(p2)
            if x<self.row-1 and y>0 and pointMap.visit(self, x+1, y-1):
                p2 = point(x+1, y-1)
                if pointMap.getValue(self, p2) == 1:
                    mark.append((x+1,y-1))
                    pend.append(p2)
            if x<self.row-1 and y<self.col-1 and pointMap.visit(self, x+1, y+1):
                p2 = point(x+1, y+1)
                if pointMap.getValue(self, p2) == 1:
                    mark.append((x+1,y+1))
                    pend.append(p2)
            '''
        return mark

inp = vae1.input    # input placeholder
outputs = [layer.output for layer in vae1.layers]       # all layer outputs
functor = K.function([inp] + [K.learning_phase()], outputs ) # evaluation function
decode1 = np.zeros((50000, 64, 64, 1))

for i in range(500):
    layer_outs = functor([train_Img[i*100:(i+1)*100], 1.])
    decode1[i*100:(i+1)*100]=layer_outs[15]
    
#h1 = train_Img[:50000].reshape((50000, 64*64))
h2 = decode1.reshape((10000, 64*64))
hpcol = np.dstack(h1, h2))

from sklearn.cluster import MiniBatchKMeans
from scipy.cluster.vq import whiten

kmeans = MiniBatchKMeans(n_clusters=2, compute_labels=False)

    
h1 = train_Img[:50000].reshape((50000,64*64))
h2 = decode1[:50000].reshape((50000,64*64))
#h3 = decode2[5000:5100, :,:,:].reshape((100, 64*64))
hypercol = np.dstack((h1, h2))

new_Img = np.zeros((50000, 64, 64, 1))

add = 0
for img_idx in range(50000):
    if img_idx+add==49999:
        break
    sample = h2[img_idx+add].reshape((4096,1))
        
    aggregate_hpcol = whiten(sample)
    kmeans.fit(sample)
        
    pred = kmeans.predict(sample)
    pred = pred.reshape((64,64))
        
    if pred.sum()>64*32:
        if pred[32, 32] == 0:
            pred = 1-pred
        else:
            add += 1
            continue

    pm = pointMap(pred)
    mark = pm.getCluster()

    pic = np.zeros((64, 64,1))
    for p in mark:
        pic[p[0], p[1]] = train_Img[img_idx+add, p[0], p[1]]

    new_Img[img_idx] = pic
    img_idx += 1       
    
    
from keras.layers import Input, Dense, Conv2D, MaxPooling2D, UpSampling2D, Flatten, Activation, Reshape
from keras.optimizers import SGD, Adadelta, Adagrad,Adam, rmsprop
from keras import objectives
from keras.callbacks import TensorBoard
from keras import backend as K
from keras.models import Model
from keras.losses import binary_crossentropy
from keras.callbacks import EarlyStopping
from keras.layers.advanced_activations import LeakyReLU

#encoder:
input_img = Input(shape=(64,64,1))

conv1_1 = Conv2D(32, (5, 5), activation='relu', padding='valid',kernel_initializer='normal')(input_img)
conv1_2 = Conv2D(32, (3, 3), activation='relu', padding='valid',kernel_initializer='normal')(conv1_1)
maxpool_1 = MaxPooling2D((2, 2))(conv1_2)

conv2_1 = Conv2D(64, (3, 3), activation='relu', padding='same',kernel_initializer='normal')(maxpool_1)
conv2_2 = Conv2D(64, (3, 3), activation='relu', padding='same',kernel_initializer='normal')(conv2_1)
conv2_3 = Conv2D(64, (3, 3), activation='relu', padding='same',kernel_initializer='normal')(conv2_2)
maxpool_2 = MaxPooling2D((2, 2))(conv2_3)

conv3_1 = Conv2D(128, (3, 3), activation='relu', padding='same',kernel_initializer='normal')(maxpool_2)
conv3_2 = Conv2D(128, (3, 3), activation='relu', padding='same',kernel_initializer='normal')(conv3_1)
conv3_3 = Conv2D(128, (3, 3), activation='relu', padding='same',kernel_initializer='normal')(conv3_2)
maxpool_3 = MaxPooling2D((2, 2))(conv3_3)

fc_1 = Flatten()(maxpool_2)
fc_2 = Dense(2048, activation='relu')(fc_1)
fc_3 = Dense(2048, activation='relu')(fc_2)
predictions = Dense(1, activation='sigmoid')(fc_3)

EarlyStopping = EarlyStopping(monitor='val_loss', min_delta=0, patience=10, verbose=0, mode='auto')

cnn = Model(inputs=input_img, outputs=predictions)
cnn.compile(optimizer='rmsprop', loss='binary_crossentropy', metrics=['accuracy'])

cnn.fit(new_Img[:45000], Class[:45000],
        shuffle=True,
        epochs=100,
        batch_size=100,
        validation_data=(new_Img[45000:50000], Class[45000:50000]), callbacks=[EarlyStopping]
       )