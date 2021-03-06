#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 17-9-29 下午3:56
# @Author  : Luo Yao
# @Site    : http://github.com/TJCVRS
# @File    : demo_shadownet.py
# @IDE: PyCharm Community Edition
"""
Use shadow net to recognize the scene text
"""
import tensorflow as tf
import os.path as ops
import numpy as np
import cv2
import argparse
import math
import os
import matplotlib.pyplot as plt
try:
    from cv2 import cv2
except ImportError:
    pass

from crnn_model import crnn_model
from global_configuration import config
from local_utils import log_utils, data_utils

logger = log_utils.init_logger()


def init_args():
    """

    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--image_path', type=str, help='Where you store the image',
                        default='data/test_images/test_02.jpg')
    parser.add_argument('--weights_path', type=str, help='Where you store the weights',
                        default='model/shadownet_2018-06-22-06-04-22.ckpt-2311')

    return parser.parse_args()


def recognize(image_path, weights_path, is_vis=False):
    """

    :param image_path:
    :param weights_path:
    :param is_vis:
    :return:
    """
    tf.reset_default_graph()
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    image = cv2.resize(image, (100, 32))
    image = np.expand_dims(image, axis=0).astype(np.float32)

    inputdata = tf.placeholder(dtype=tf.float32, shape=[1, 32, 100, 3], name='input')
    input_labels = tf.SparseTensor(tf.placeholder(tf.int64, shape=[None, 2]) , tf.placeholder(tf.int32, [None]), tf.placeholder(tf.int64, [2]))
    net = crnn_model.ShadowNet(phase='Test', hidden_nums=256, layers_nums=2, seq_length=25, num_classes=96)

    with tf.variable_scope('shadow'):
        net_out = net.build_shadownet(inputdata=inputdata)
    cost = tf.nn.ctc_loss(labels=input_labels, inputs=net_out, sequence_length=25*np.ones(1))
    decodes, _ = tf.nn.ctc_beam_search_decoder(inputs=net_out, sequence_length=25*np.ones(1), merge_repeated=False)

    decoder = data_utils.TextFeatureIO()

    # config tf session
    sess_config = tf.ConfigProto()
    sess_config.gpu_options.per_process_gpu_memory_fraction = config.cfg.TRAIN.GPU_MEMORY_FRACTION
    sess_config.gpu_options.allow_growth = config.cfg.TRAIN.TF_ALLOW_GROWTH

    # config tf saver
    saver = tf.train.Saver()

    sess = tf.Session(config=sess_config)

    with sess.as_default():

        saver.restore(sess=sess, save_path=weights_path)

        preds = sess.run(decodes, feed_dict={inputdata: image})
        preds = decoder.writer.sparse_tensor_to_str(preds[0])

        
        sparse = decoder.reader.str_to_sparse_tensor(preds)
        
        loss = sess.run(cost, feed_dict={inputdata: image,input_labels: sparse})

        
        prob = math.exp(-loss)
        print("image:",image_path," | label:",preds[0]," | score:",prob)
        #logger.info('Predict image {:s} label {:s}'.format(ops.split(image_path)[1], preds[0]))

        if is_vis:
            plt.figure('CRNN Model Demo')
            plt.imshow(cv2.imread(image_path, cv2.IMREAD_COLOR)[:, :, (2, 1, 0)])
            plt.show()

        sess.close()

    return


if __name__ == '__main__':
    # Inti args
    args = init_args()
    #if not ops.exists(args.image_path):
        #raise ValueError('{:s} doesn\'t exist'.format(args.image_path))
    for file in os.listdir("data/test_images"):
            print("processing:"+str(file))
            # recognize the image
            recognize(image_path="data/test_images/"+file, weights_path=args.weights_path)
    # recognize the image
    #recognize(image_path=args.image_path, weights_path=args.weights_path)
