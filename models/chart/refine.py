""" Module for refining classification results

    Args:
        --overwrite: overwrite or not
        ori: origin
        lc: MODIS land cover
        vcf: MODIS VCF
        des: destination

"""
import os
import argparse
import numpy as np

from osgeo import gdal

from ...common import log, get_files, show_progress
from ...io import stack2array, stackGeo, array2stack


def refine_results(ori, lc, vcf, des, overwrite=False):
    """ refine classification results

    Args:
        ori (str): path and filename of classification results
        lc (str): path and filename of MODIS land cover maps
        vcf (str): path and filename of MODIS VCF
        des (str): place to save output map
        overwrite (bool): overwrite or not

    Returns:
        0: successful
        1: error due to des
        2: error when reading inputs
        3: error during processing
        4: error writing output

    """
    m2c = [0,2,2,4,4,5,10,10,9,9,10,11,12,13,12,16,16,25,0,0,0,0,0,0,0,0,0,0,0]
    # check if output already exists
    if (not overwrite) and os.path.isfile(des):
        log.error('{} already exists.'.format(os.path.basename(des)))
        return 1

    # read input image
    log.info('Reading input maps...')
    try:
        r = stack2array(ori)
        lc = stack2array(lc)
        vcf = stack2array(vcf)
        lc = np.kron(lc, np.ones((2,2,1))).astype(lc.dtype)
    except:
        log.error('Failed to read input maps.')
        return 2

    # read geo info
    log.info('Reading geo information...')
    try:
        geo = stackGeo(ori)
    except:
        log.error('Failed to read geo info.')
        return 2

    # refine classification results
    log.info('Refining maps...')
    try:
        (lines, samples, nband) = r.shape
        for i in range(0,lines):
            for j in range(0, samples):
                p = r[i, j, :]
                p_class = np.unique(p)[0]

                plc = np.zeros(19, dtype=int)
                plc[0:18] = lc[i, j, 0:18]
                plc[18] = lc[i, j, -1]
                plc_label = np.bincount(plc).argmax()
                plcn = len(np.unique(plc))

                pvcf = np.zeros(19, dtype=int)
                pvcf[0:18] = vcf[i, j, 1:19]
                pvcf[18] = vcf[i, j, -1]
                mvcf = int(pvcf.mean())

                # fix short plantation in beginning
                if p[3] != 18:
                    if p[0] == 18:
                        p[0] = p[3]
                    if p[1] == 18:
                        p[1] = p[3]
                    if p[2] == 18:
                        p[2] = p[3]
                    r[i, j, :] = p

                # deel with unclassified
                if max(p == 0) == 1:
                    uclc = plc[p == 0]
                    p_label = m2c[np.bincount(uclc).argmax()]
                    # uc in the beginning
                    if (p[0] == 0):
                        if p_label in [13, 25]:
                            p[p == 0] = p_label
                        else:
                            p[p == 0] = p[p != 0][0]
                    # uc in the end
                    elif p[-1] == 0:
                        if p_label in [13, 25]:
                            p[p == 0] = p_label
                        else:
                            p[p == 0] = p[p != 0][-1]
                    # mostly uc
                    elif sum(p == 0) > 10:
                        p[p == 0] = p_label
                    # single uc
                    elif sum(p == 0) <= 10:
                        for k in range(0, len(p)):
                            if p[k] == 0:
                                p[k] = p[k - 1]
                    r[i, j, :] = p

                # urban barren fix
                if sum((p == 13) & (plc == 16)) >= 5:
                    p[(p == 13) & (plc == 16)] = 16
                    r[i, j, :] = p
                # urban grassland fix
                if sum((p == 13) & (plc == 10)) >= 5:
                    p[(p == 13) & (plc == 10)] = 10
                    r[i, j, :] = p

                # refinement 2
                p = r[i, j, :]
                psta = toSta(p[2], p[13])
                p_label = -1
                if psta == 3:
                    if (plc_label <= 5):
                        p_label = m2c[plc_label]
                elif psta == 6:
                    if (plc_label == 10) & (plcn == 1):
                        p_label = 10
                elif psta == 7:
                    if (plc_label == 10) & (mvcf > 10) & (plcn == 1):
                        p_label = 10
                elif psta == 9:
                    if (plc_label in [2, 4]) & (mvcf >= 40):
                        p_label = m2c[plc_label]
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
                    if (plc_label == 2) & (mvcf > 40) & (p[13] == 12):
                        p[p == 12] = 18
                elif psta == 11:
                    if (plc_label == 2) & (p[2] in [2, 9]) & (p[13] == 18):
                        if plcn == 1:
                            p_label = 2
                        if (plcn == 2) & (mvcf >= 45):
                            p_label = 2
                    if (plc_label in [10, 12]) & (p[13] == 18):
                        if (plcn <= 2) & (mvcf <= 10) & (p[2] in [12, 9]):
                            p_label = 12
                        if (plcn >= 3):
                            p[p == 18] = 12
                    if (plc_label == 8):
                        if (plcn == 1):
                            p_label = 9
                        if (plcn == 2) & (mvcf < 40):
                            p_label = 9
                elif psta == 12:
                    if (plc_label == 13) & (plcn == 1):
                        if (mvcf <= 5) & (p[2] == 12):
                            p_label = 13
                        if (mvcf > 10) & (p[2] == 17):
                            p_label = 13
                elif psta == 13:
                    if (plc_label == 11) & (plcn <= 2):
                        p_label = 19
                    if (plc_label == 2) & (plcn <= 2) & (mvcf > 40) & (p[2] == 2):
                        p_label = 2
                elif psta == 14:
                    if (plc_label in [10, 12]) & (p[2] in [10, 12]):
                        if mvcf < 15:
                            p_label = 12
                        else:
                            p_label = 9
                    if (plc_label in [8, 9]) & (p[2] in [10, 12]):
                        p_label = 9
                elif psta == 15:
                    if (plcn == 1) & (p[2] in [12, 17]) & (p[13] in [12, 17]):
                        p_label = p[2]
                    if (plcn <= 2) & (p[2] == 18) & (p[13] in [2, 9]):
                        if (plc_label in [2, 4]) & (mvcf >= 40):
                            p_label = plc_label
                        if (plc_label == 8) & (mvcf >= 45):
                            p_label = 2
                        if (plc_label in [8, 9]) & (mvcf < 45):
                            p_label = 9
                        if (plc_label in [12, 10]) & (mvcf > 20):
                            p_label = 9
                    if (mvcf > 40) & (plcn <= 2) & (p[2] == 9) & (p[13] == 2):
                        p_label = 9
                    if (p[2] in [10, 16]) & (p[13] in [10, 16]):
                        p_label = np.bincount(p).argmax()
                if p_label > 0:
                    r[i, j, :] = p_label

            progress = show_progress(i, lines, 5)
            if progress >= 0:
                log.info('{}% done.'.format(progress))
    except:
        log.error('Failed to refine results.')
        return 3

    # write output
    log.info('Writing output...')
    try:
        array2stack(r, geo, des, 'NA', 255, gdal.GDT_Int16, overwrite, 'GTiff',
                    ['COMPRESS=LZW'])
    except:
        log.error('Failed to write output to {}'.format(des))
        return 4

    # done
    log.info('Process completed.')
    return 0


def toSta(x1, x2):
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


if __name__ == '__main__':
    # parse options
    parser = argparse.ArgumentParser()
    parser.add_argument('--overwrite', action='store_true',
                        help='overwrite or not')
    parser.add_argument('ori', default='./', help='classification results')
    parser.add_argument('lc', default='./', help='MODIS land cover maps')
    parser.add_argument('vcf', default='./', help='MODIS VCF')
    parser.add_argument('des', default='./', help='destination')
    args = parser.parse_args()

    # print logs
    log.info('Start comparing...')
    log.info('Classification results: {}'.format(args.ori))
    log.info('MODIS land cover: {}'.format(args.lc))
    log.info('MODIS VCF: {}'.format(args.vcf))
    log.info('Saving as {}'.format(args.des))
    if args.overwrite:
        log.info('Overwriting old files.')

    # run function to refine classification results
    refine_results(args.ori, args.lc, args.vcf, args.des, args.overwrite)
