""" Module for assessing accuracy for CHART
"""
import os
import numpy as np

from ....common import conf_mat, accuracy_assessment, numeric_example


class accuracy:
    wd = '/Users/xjtang/Desktop/chart/'
    input = os.path.join(wd, 'mekong_all.csv')
    C2S = [0,1,1,0,1,1,0,0,3,3,4,5,2,6,2,0,7,2,9,5,5,2,0,0,0,8]
    C2M = [0,1,1,0,1,1,0,0,3,3,4,5,2,6,2,0,7,2,2,5,5,2,0,0,0,8]
    C2R = [-1,9,9,8,8,85,-1,-1,12,12,6,20,6,0,6,-1,0,20,85,20,20,0,-1,-1,-1,0]

    def __init__(self):
        self.r = np.genfromtxt(self.input, delimiter=',', dtype=None, names=True)
        self.r2 = self.ref2annual(self.r)
        self.sc = np.transpose(np.array(((1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,
                                13, 14, 15), (4051455, 3826433, 3372155, 955536,
                                145348, 43714, 267604, 1083771, 1467077, 288310,
                                914216, 16064, 21603, 32452, 650649)),
                                dtype='int32'))
        self.map = self.toSta(self.r['map_2003'], self.r['map_2014'])
        self.sta = self.r['STRATUM']
        self.ref = self.toSta(self.r2[:,2], self.r2[:,13])
        self.aa = accuracy_assessment(self.sta, self.ref, self.map, self.sc)
        self.cf = conf_mat(self.ref, self.map)

    def toSta(self, x1, x2):
        y = np.zeros(len(x1), dtype='int8')
        for i in range(0, len(x1)):
            if x1[i] == x2[i]:
                y[i] = self.C2S[x1[i]]
            else:
                L1C = self.C2S[x1[i]]
                L2C = self.C2S[x2[i]]
                if ((L2C == 2) & (L1C != 2)):
                    y[i] = 10
                elif L2C == 9:
                    y[i] = 11
                elif L2C == 6:
                    y[i] = 12
                elif ((L1C in [1, 3]) & (L2C in [4, 5, 7, 8])):
                    y[i] = 13
                elif ((L1C in [2, 4, 5, 6, 7, 8]) & (L2C in [1, 3])):
                    y[i] = 14
                else:
                    y[i] = 15
        return y

    def toParent(self, x):
        y = np.zeros(len(x), dtype='int8')
        for i in range(0, len(x)):
            y[i] = self.C2M[x[i]]
        return y

    def ref2annual(self, x):
        y = np.zeros((len(x), 16), dtype='int8')
        for i in range(0, len(x)):
            y[i, :] = x[i]['CID1']
            if x[i]['ED1'] > 0:
                t = x[i]['ED1']
                t = t//1000 - 2000
                y[i, t:] = x[i]['CID2']
                if x[i]['ED2'] > 0:
                    t = x[i]['ED2']
                    t = t//1000 - 2000
                    y[i, t:] = x[i]['CID3']
        return y

    def toRootDepth(self, x):
        y = np.zeros(len(x), dtype='int8')
        for i in range(0, len(x)):
            y[i] = self.C2R[x[i]]
        return y
