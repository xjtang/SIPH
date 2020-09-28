""" Module for estimate area for CHART
"""
import os
import numpy as np

from ....common import conf_mat, accuracy_assessment, numeric_example


class accuracy:
    C2S = [0,1,1,0,1,1,0,0,3,3,4,5,2,6,2,0,7,2,9,5,5,2,0,0,0,8]
    S2P = [0,1,1,0,1,1,0,0,3,3,4,5,2,6,2,0,7,2,2,5,5,2,0,0,0,8]
    C2R = [-1,9,9,8,8,85,-1,-1,12,12,6,20,6,0,6,-1,0,20,85,20,20,0,-1,-1,-1,0]
    M2C = [0,2,2,4,4,5,10,10,9,9,10,11,12,13,12,16,16,25,0,0,0,0,0,0,0,0,0,0,0]

    def __init__(self, _file, site='mekong'):
        if site == 'mekong':
            self.wd = '/Users/xjtang/Applications/GoogleDrive/Temp/chart/mekong/sheets/'
            self.sc = np.transpose(np.array(((1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
                                    12, 13, 14, 15), (4051455, 3826433, 3372155,
                                    955536, 145348, 43714, 267604, 1083771,
                                    1467077, 288310, 914216, 16064, 21603,
                                    32452, 650649)), dtype='int32'))
        else:
            self.wd = '/Users/xjtang/Applications/GoogleDrive/Temp/chart/krishna/sheets/'
            self.sc = np.transpose(np.array(((1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12,
                                    14, 15), (1415353, 8460949, 819367, 137681,
                                    57075, 23484, 18369, 99537, 155367, 13795,
                                    27370, 7522, 30297)), dtype='int32'))
        self.input = os.path.join(self.wd, _file)
        self.site = site
        self.r = np.genfromtxt(self.input, delimiter=',', dtype=None, names=True)
        self.r2 = self.ref2annual(self.r)

        self.map1 = self.toSta(self.r['map_2003'], self.r['map_2014'])
        self.sta = self.r['STRATUM']
        self.ref1 = self.toSta(self.r2[:, 2], self.r2[:, 13])
        self.aa1 = accuracy_assessment(self.sta, self.ref1, self.map1, self.sc)
        self.cf1 = conf_mat(self.ref1, self.map1)

        self.map2 = self.toSta(self.r['map_2001'], self.r['map_2016'])
        self.ref2 = self.toSta(self.r2[:, 0], self.r2[:, 15])
        self.aa2 = accuracy_assessment(self.sta, self.ref2, self.map2, self.sc)
        self.cf2 = conf_mat(self.ref2, self.map2)

        #self.annualAg = self.aea(2)
        #self.annualPlant = self.aea(9)
        #self.annual2 = self.aec(11)
        #self.annualDef = self.adf()
        #self.annualRgr = self.arg()

    def aea(self, _class=2):
        x = np.zeros((2, 16))
        for i in range(0, 16):
            _map = self.toSta(self.r['map_{}'.format(2001 + i)],
                                self.r['map_{}'.format(2001 + i)])
            _ref = self.toSta(self.r2[:, i], self.r2[:, i])
            aa = accuracy_assessment(self.sta, _ref, _map, self.sc)
            x[0, i] = aa['area'][_class - 1]
            x[1, i] = aa['se_area'][_class - 1]
        return x

    def aec(self, _class=2):
        x = np.zeros((2, 17))
        for i in range(0, 17, 2):
            try:
                _map = self.toSta(self.r['map_{}'.format(2001 + i)],
                                    self.r['map_{}'.format(2003 + i)])
                _ref = self.toSta(self.r2[:, i], self.r2[:, i + 2])
                aa = accuracy_assessment(self.sta, _ref, _map, self.sc)
                cls = np.sort(np.unique(np.array((_ref, _map))))
                if _class in cls:
                    x[0, i] = aa['area'][cls == _class]
                    x[1, i] = aa['se_area'][cls == _class]
            except:
                print(i)
        return x

    def saveaaa(self, _aaa, _file='aaa'):
        np.savetxt(os.path.join(self.wd, '{}.csv'.format(_file)), _aaa,
                    delimiter=',')
        return 0

    def toParent(self, x):
        y = np.zeros(len(x), dtype='int8')
        for i in range(0, len(x)):
            y[i] = self.S2P[x[i]]
        return y

    def toSta(self, x1, x2, CT=False):
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
                    if self.site == 'mekong':
                        y[i] = 11
                    else:
                        y[i] = 11
                elif L2C == 6:
                    y[i] = 12
                elif ((L1C in [1, 3]) & (L2C in [4, 5, 7, 8])):
                    if self.site == 'mekong':
                        y[i] = 13
                    else:
                        y[i] = 13
                elif ((L1C in [2, 4, 5, 6, 7, 8]) & (L2C in [1, 3])):
                    y[i] = 14
                else:
                    y[i] = 15
        if CT:
            y[y == 3] = 1
            y[y == 9] = 1
        return y

    def ref2annual(self, x):
        y = np.zeros((len(x), 19), dtype='int8')
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

    def toDef(self, x1, x2):
        y = np.zeros(len(x1), dtype='int8')
        for i in range(0, len(x1)):
            if (x1[i] in [2,4,5,9,18,19,20]) & (x2[i] not in [2,4,5,9,18,19,20]):
                y[i] = 1
            elif (x1[i] in [2,4,5,19,20]) & (x2[i] in [9,18]):
                y[i] = 1
        return y

    def adf(self):
        x = np.zeros((2, 17))
        for i in range(0, 17, 2):
            try:
                _map = self.toDef(self.r['map_{}'.format(2001 + i)],
                                    self.r['map_{}'.format(2003 + i)])
                _ref = self.toDef(self.r2[:, i], self.r2[:, i + 1])
                aa = accuracy_assessment(self.sta, _ref, _map, self.sc)
                cls = np.sort(np.unique(np.array((_ref, _map))))
                if 1 in cls:
                    x[0, i] = aa['area'][cls == 1]
                    x[1, i] = aa['se_area'][cls == 1]
            except:
                print(i)
        return x

    def toRgr(self, x1, x2):
        y = np.zeros(len(x1), dtype='int8')
        for i in range(0, len(x1)):
            if (x1[i] not in [2,4,5,9,18,19,20]) & (x2[i] in [2,4,5,9,18,19,20]):
                y[i] = 1
            elif (x1[i] in [2,4,5]) & (x2[i] == 9):
                y[i] = 1
            elif (x1[i] != 18) &  (x2[i] == 18):
                y[i] = 1
        return y

    def arg(self):
        x = np.zeros((2, 15))
        for i in range(0, 15):
            _map = self.toRgr(self.r['map_{}'.format(2001 + i)],
                                self.r['map_{}'.format(2002 + i)])
            _ref = self.toRgr(self.r2[:, i], self.r2[:, i + 1])
            aa = accuracy_assessment(self.sta, _ref, _map, self.sc)
            cls = np.sort(np.unique(np.array((_ref, _map))))
            if 1 in cls:
                x[0, i] = aa['area'][cls == 1]
                x[1, i] = aa['se_area'][cls == 1]
        return x

    def AtoB(self, x1, x2, a=[2,4,5], b=[7]):
        y = np.zeros(len(x1), dtype='int8')
        for i in range(0, len(x1)):
            if (x1[i] in a) & (x2[i] in b):
                y[i] = 1
        return y

    def EAofAtoB(self, a=[2,4,5], b=[8]):
        _map = self.AtoB(self.r['map_2001'], self.r['map_2016'], a, b)
        _ref = self.AtoB(self.r2[:, 0], self.r2[:, 15], a, b)
        aa = accuracy_assessment(self.sta, _ref, _map, self.sc)
        return (aa['area'], aa['se_area'])

    def AAofAtoB(self, a=[2,4,5], b=[7]):
        x = np.zeros((2, 15))
        for i in range(0, 15):
            _map = self.AtoB(self.r['map_{}'.format(2001 + i)],
                                self.r['map_{}'.format(2002 + i)], a, b)
            _ref = self.AtoB(self.r2[:, i], self.r2[:, i + 1], a, b)
            try:
                aa = accuracy_assessment(self.sta, _ref, _map, self.sc)
                x[0, i] = aa['area'][1]
                x[1, i] = aa['se_area'][1]
            except:
                print(i)
        return x

    def OAofAtoB(self, a=[2,4,5], b=[7], i=0):
        _map = self.AtoB(self.r['map_{}'.format(2001+i)],
                            self.r['map_{}'.format(2016-i)], a, b)
        _ref = self.AtoB(self.r2[:, 0+i], self.r2[:, 15-i], a, b)
        aa = accuracy_assessment(self.sta, _ref, _map, self.sc)
        cls = np.sort(np.unique(np.array((_ref, _map))))
        if 1 in cls:
            return (aa['area'][cls == 1], aa['se_area'][cls == 1])
        else:
            return (0, 0)
