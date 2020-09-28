""" Module for assessing accuracy of maps from Landsat
"""
import os
import numpy as np

from ....common import conf_mat, accuracy_assessment, numeric_example


class accuracy:
    C2S = [0,1,1,0,1,1,0,0,3,3,4,5,2,6,2,0,7,2,9,5,5,2,0,0,0,8]
    sc = np.transpose(np.array(((1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,
                            14, 15), (4051455, 3826433, 3372155, 955536, 145348,
                            43714, 267604, 1083771, 1467077, 288310, 914216,
                            16064, 21603, 32452, 650649)), dtype='int32'))

    def __init__(self):
        self.wd = '/Users/xjtang/Applications/GoogleDrive/Temp/chart/landsat/sheets/'
        self.changeFile = os.path.join(self.wd, 'change.csv')
        self.changeTable = np.genfromtxt(self.changeFile, delimiter=',', dtype=None, names=True)
        self.change = self.resample(self.changeTable, True)

        #self.map2003File = os.path.join(self.wd, 'map2003.csv')
        #self.map2014File = os.path.join(self.wd, 'map2014.csv')
        #self.map2003Table = np.genfromtxt(self.map2003File, delimiter=',', dtype=None, names=True)
        #self.map2014Table = np.genfromtxt(self.map2014File, delimiter=',', dtype=None, names=True)
        #self.map2003 = self.resample(self.map2003Table, False)
        #self.map2014 = self.resample(self.map2014Table, False)
        #self.change2 = self.getChange(self.map2003, self.map2014)

        self.refFile = os.path.join(self.wd, 'ref.csv')
        self.refTable = np.genfromtxt(self.refFile, delimiter=',', dtype=None, names=True)
        self.refAnnual = self.ref2annual(self.refTable)
        self.ref = self.toSta(self.refAnnual[:, 2], self.refAnnual[:, 13])
        self.sta = self.refTable['STRATUM']

        self.aa = accuracy_assessment(self.sta, self.ref, self.change, self.sc)
        self.cf = conf_mat(self.ref, self.change)
        #self.aa2 = accuracy_assessment(self.sta, self.ref, self.change2, self.sc)
        #self.cf2 = conf_mat(self.ref, self.change2)

        self.check = np.zeros((len(self.change), 18))
        self.check[:, 0] = self.changeTable['PID']
        self.check[:, 1] = self.change
        self.check[:, 2] = self.ref
        self.check[:, 3] = self.changeTable['Forest']
        self.check[:, 4] = self.changeTable['Ag']
        self.check[:, 5] = self.changeTable['Savanna']
        self.check[:, 6] = self.changeTable['Grassland']
        self.check[:, 7] = self.changeTable['Wetland']
        self.check[:, 8] = self.changeTable['Urban']
        self.check[:, 9] = self.changeTable['Barren']
        self.check[:, 10] = self.changeTable['Water']
        self.check[:, 11] = self.changeTable['Plantation']
        self.check[:, 12] = self.changeTable['toAg']
        self.check[:, 13] = self.changeTable['toPlant']
        self.check[:, 14] = self.changeTable['toUrban']
        self.check[:, 15] = self.changeTable['forestToOt']
        self.check[:, 16] = self.changeTable['Regrow']
        self.check[:, 17] = self.changeTable['Others']

    def saveCheck(self, _file='check.csv'):
        np.savetxt(os.path.join(self.wd, _file), self.check,
                    delimiter=',', fmt='%f')
        return 0

    def resample(self, map, change=False):
        y = np.zeros(len(map), dtype='int8') - 99
        for i in range(0, len(map)):
            x = map[i]
            wet = x['Water'] + x['Wetland']
            tree = x['Forest'] + 0.6 * x['Savanna']
            urban = x['Urban'] + x['Barren']
            allchange = x['toAg'] + x['toPlant'] + x['toUrban'] + x['forestToOt'] + x['Regrow'] + x['Others']
            if x['Water'] >= 0.6:
                y[i] = 8
            elif (x['Urban'] >= 0.3) | ((x['Urban'] >= 0.1) & (urban >= 0.6)):
                y[i] = 6
            elif x['Plantation'] >= 0.7:
                y[i] = 9
            elif tree >= 0.6:
                y[i] = 1
            elif x['Ag'] >= 0.3:
                y[i] = 2
            elif tree + x['Plantation'] >= 0.3:
                y[i] = 3
            elif wet > 0.4:
                y[i] = 5
            elif x['Grassland'] + tree > 0.3:
                y[i] = 4
            elif x['Barren'] > 0.7:
                y[i] = 7
            else:
                a = [x['Forest'], x['Ag'], x['Savanna'], x['Grassland'], x['Wetland'],
                        x['Urban'], x['Barren'], x['Water'], x['Plantation']]
                y[i] = a.index(max(a)) + 1
            if change:
                if (x['Ag'] < 0.3) & (x['Ag'] + x['toAg'] >= 0.3) & (x['toAg'] > 0.1):
                    y[i] = 10
                elif (x['toPlant'] + x['Plantation'] > 0.6) & (x['toPlant'] > 0.15):
                    y[i] = 11
                elif (urban < 0.3) & (x['toUrban'] > 0.05):
                    y[i] = 12
                elif (allchange > 0.3) & (x['forestToOt'] > 0.15):
                    y[i] = 13
                elif (allchange > 0.3) & (x['Regrow'] > 0.15):
                    y[i] = 14
                elif (allchange > 0.3) & (x['Others'] > 0.15):
                    y[i] = 15
        return y

    def getChange(self, x1, x2):
        y = np.zeros(len(x1), dtype='int8')
        for i in range(0, len(x1)):
            if x1[i] == x2[i]:
                y[i] = x1[i]
            else:
                if ((x1[i] == 2) & (x2[i] != 2)):
                    y[i] = 10
                elif x2[i] == 9:
                    y[i] = 11
                elif x2[i] == 6:
                    y[i] = 12
                elif ((x1[i] in [1, 3]) & (x2[i] in [4, 5, 7, 8])):
                    y[i] = 13
                elif ((x1[i] in [2, 4, 5, 6, 7, 8]) & (x2[i] in [1, 3])):
                    y[i] = 14
                else:
                    y[i] = 15
        return y

    def saveCF(self, cf, _file='conf_mat.csv'):
        np.savetxt(os.path.join(self.wd, _file), cf, delimiter=',', fmt='%d')
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
