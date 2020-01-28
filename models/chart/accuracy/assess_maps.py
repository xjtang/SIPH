""" Module for assessing accuracy for CHART
"""
import os
import numpy as np

from ....common import conf_mat, accuracy_assessment, numeric_example


class accuracy:
    wd = '/Users/xjtang/Applications/GoogleDrive/Temp/chart/mekong/sheets/'
    C2S = [0,1,1,0,1,1,0,0,3,3,4,5,2,6,2,0,7,2,9,5,5,2,0,0,0,8]
    C2M = [0,1,1,0,1,1,0,0,3,3,4,5,2,6,2,0,7,2,2,5,5,2,0,0,0,8]
    C2R = [-1,9,9,8,8,85,-1,-1,12,12,6,20,6,0,6,-1,0,20,85,20,20,0,-1,-1,-1,0]

    def __init__(self, _file):
        self.input = os.path.join(self.wd, _file)
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

        self.map2 = self.refine(self.r['map_2003'], self.r['map_2014'],
                                self.r['lc'], self.r['vcf'], self.r['lcnc'])
        self.aa2 = accuracy_assessment(self.sta, self.ref, self.map2, self.sc)
        self.cf2 = conf_mat(self.ref, self.map2)

        self.map3 = self.toRootDepth(self.r['map_2014'])
        self.ref3 = self.toRootDepth(self.r2[:, 13])
        self.aa3 = accuracy_assessment(self.sta, self.ref3, self.map3, self.sc)
        self.cf3 = conf_mat(self.ref3, self.map3)

        self.check = np.zeros((len(self.map), 3), np.int16)
        self.check[:, 0] = self.r['SID']
        self.check[:, 1] = self.map
        self.check[:, 2] = self.ref

    def saveCF(self, cf):
        np.savetxt(os.path.join(self.wd, 'conf_mat.csv'), cf, delimiter=',',
                    fmt='%d')
        return 0

    def saveCheck(self):
        np.savetxt(os.path.join(self.wd, 'check.csv'), self.check,
                    delimiter=',', fmt='%d')
        return 0

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

    def refine(self, map1, map2, lc, vcf, nc):
        m2c = [0,2,2,4,4,5,10,10,9,9,10,11,12,13,12,16,16,25,0,0,0,0,0,0,0,0,0,0,0]
        for i in range(0, len(map1)):
            plc_label = lc[i]
            plcn = nc[i]
            psta = self.toSta2(map1[i], map2[i])
            mvcf = vcf[i]
            p_label = -1
            if psta == 3:
                if (plc_label in [2, 4, 5]):
                    p_label = plc_label
            elif psta == 6:
                if (plc_label == 10) & (plcn == 1):
                    p_label = 10
            elif psta == 7:
                if (plc_label == 10) & (mvcf > 10) & (plcn == 1):
                    p_label = 10
            elif psta == 9:
                if (plc_label in [2, 4]) & (mvcf >= 40):
                    p_label = plc_label
                if (plc_label == 12) & (plcn == 1):
                    p_label = 12
                if (plc_label in [8, 9]):
                    if plcn == 1:
                        p_label = 9
                    if (plcn == 2) & (mvcf <= 20):
                        p_label = 9
            elif psta == 10:
                if (plc_label == 10) & (plcn == 1):
                    p_label = 12
                if (plc_label == 12) & (plcn <= 2):
                    p_label = 12
                if (plc_label == 9) & (plcn == 1):
                    p_label = 9
                if (plc_label == 2) & (mvcf > 40) & (map2[i] == 12):
                    map2[i] = 18
            elif psta == 11:
                if (plc_label == 2) & (map1[i] in [2, 9]) & (map2[i] == 18):
                    if plcn == 1:
                        p_label = 2
                    if (plcn == 2) & (mvcf >= 45):
                        p_label = 2
                if (plc_label in [10, 12]) & (map2[i] == 18):
                    if (plcn <= 2) & (mvcf <= 10) & (map1[i] in [12, 9]):
                        p_label = 12
                    if (plcn >= 3):
                        map2[i] = 12
                if (plc_label == 8):
                    if (plcn == 1):
                        p_label = 9
                    if (plcn == 2) & (mvcf < 40):
                        p_label = 9
            elif psta == 12:
                if (plc_label == 13) & (plcn == 1):
                    if (mvcf <= 5) & (map1[i] == 12):
                        p_label = 13
                    if (mvcf > 10) & (map1[i] == 17):
                        p_label = 13
            elif psta == 13:
                if (plc_label == 11) & (plcn <= 2):
                    p_label = 19
                if (plc_label == 2) & (plcn <= 2) & (mvcf > 40) & (map1[i] == 2):
                    p_label = 2
            elif psta == 14:
                if (plc_label in [10, 12]) & (map1[i] in [10, 12]):
                    if mvcf < 15:
                        p_label = 12
                    else:
                        p_label = 9
                if (plc_label in [8, 9]) & (map1[i] in [10, 12]):
                    p_label = 9
            elif psta == 15:
                if (plcn == 1) & (map1[i] in [12, 17]) & (map2[i] in [12, 17]):
                    p_label = map1[i]
                if (plcn <= 2) & (map1[i] == 18) & (map2[i] in [2, 9]):
                    if (plc_label in [2, 4]) & (mvcf >= 40):
                        p_label = plc_label
                    if (plc_label == 8) & (mvcf >= 45):
                        p_label = 2
                    if (plc_label in [8, 9]) & (mvcf < 45):
                        p_label = 9
                    if (plc_label in [12, 10]) & (mvcf > 20):
                        p_label = 9
                if (mvcf > 40) & (plcn <= 2) & (map1[i] == 9) & (map2[i] == 2):
                    p_label = 9

            if p_label > 0:
                map1[i] = p_label
                map2[i] = p_label
        return self.toSta(map1, map2)

    def toSta2(self, x1, x2):
        C2S = [0,1,1,0,1,1,0,0,3,3,4,5,2,6,2,0,7,2,9,5,5,2,0,0,0,8]
        if x1 == x2:
            y = C2S[x1]
        else:
            L1C = C2S[x1]
            L2C = C2S[x2]
            if ((L2C == 2) & (L1C != 2)):
                y = 10
            elif L2C == 9:
                y = 11
            elif L2C == 6:
                y = 12
            elif ((L1C in [1, 3]) & (L2C in [4, 5, 7, 8])):
                y = 13
            elif ((L1C in [2, 4, 5, 6, 7, 8]) & (L2C in [1, 3])):
                y = 14
            else:
                y = 15
        return y
